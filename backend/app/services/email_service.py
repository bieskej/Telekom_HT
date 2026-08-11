import logging
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError, SMTPException

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.email_templates import render_email_template

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def smtp_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_host.strip()
        and settings.smtp_user
        and settings.smtp_password
    )


def html_to_plain_text(html: str) -> str:
    """Jednostavan strip HTML tagova za text/plain fallback."""
    text = _TAG_RE.sub(" ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _zapisi_email_log(
    db: Session,
    *,
    primatelj: str,
    predmet: str,
    status: str,
    html_tijelo: str | None,
    msisdn_id: int | None = None,
    error_text: str | None = None,
) -> int:
    from sqlalchemy import text

    row = db.execute(
        text(
            """
            INSERT INTO email_log (msisdn_id, primatelj, predmet, status, error_text, html_tijelo, sent_at)
            VALUES (:msisdn_id, :primatelj, :predmet, :status, :error_text, :html_tijelo,
                    CASE WHEN :status = 'poslano' THEN NOW() ELSE NULL END)
            RETURNING id
            """
        ),
        {
            "msisdn_id": msisdn_id,
            "primatelj": primatelj,
            "predmet": predmet,
            "status": status,
            "error_text": error_text,
            "html_tijelo": html_tijelo,
        },
    ).fetchone()
    db.commit()
    return row.id


def send_html_email(
    to: str,
    subject: str,
    template_name: str | None = None,
    context: dict | None = None,
    *,
    html_body: str | None = None,
    pdf_bytes: bytes | None = None,
    filename: str | None = None,
    msisdn_id: int | None = None,
    db: Session | None = None,
) -> tuple[bool, str | None, int | None]:
    """
    Šalje multipart/alternative email (HTML + text fallback).
    Svaki poziv upisuje red u email_log.
    Vraća (uspjeh, greška, log_id).
    """
    own_db = db is None
    if own_db:
        db = SessionLocal()

    if html_body is not None:
        html = html_body
    elif template_name and context is not None:
        html = render_email_template(template_name, context)
    else:
        raise ValueError("Potreban template_name+context ili html_body.")

    plain = html_to_plain_text(html)
    log_id: int | None = None

    if not smtp_configured():
        err = "SMTP nije konfiguriran"
        logger.warning("%s – preskačem slanje na %s", err, to)
        log_id = _zapisi_email_log(
            db,
            primatelj=to,
            predmet=subject,
            status="nedostaje_smtp",
            html_tijelo=html,
            msisdn_id=msisdn_id,
            error_text=err,
        )
        if own_db:
            db.close()
        return False, err, log_id

    msg = MIMEMultipart("mixed")
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain, "plain", "utf-8"))
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)

    if pdf_bytes:
        att = MIMEApplication(pdf_bytes, _subtype="pdf")
        att.add_header("Content-Disposition", "attachment", filename=filename or "privitak.pdf")
        msg.attach(att)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        logger.info("HTML email poslan na %s (%s)", to, subject)
        log_id = _zapisi_email_log(
            db,
            primatelj=to,
            predmet=subject,
            status="poslano",
            html_tijelo=html,
            msisdn_id=msisdn_id,
        )
        if own_db:
            db.close()
        return True, None, log_id
    except (SMTPAuthenticationError, SMTPException, OSError, Exception) as exc:
        err = str(exc)
        logger.error("Greška slanja emaila na %s: %s", to, err)
        log_id = _zapisi_email_log(
            db,
            primatelj=to,
            predmet=subject,
            status="greska",
            html_tijelo=html,
            msisdn_id=msisdn_id,
            error_text=err,
        )
        if own_db:
            db.close()
        return False, err, log_id


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    pdf_bytes: bytes | None = None,
    filename: str = "privitak.pdf",
) -> tuple[bool, str | None]:
    """
    Legacy plain-text slanje (zadržano za kompatibilnost).
    Za nove emailove koristite send_html_email.
    """
    if not smtp_configured():
        logger.warning("SMTP nije konfiguriran (SMTP_HOST prazan) – preskačem slanje.")
        return False, "SMTP nije konfiguriran"

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if pdf_bytes:
        att = MIMEApplication(pdf_bytes, _subtype="pdf")
        att.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(att)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls()
                server.ehlo()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        logger.info("Email uspješno poslan na %s (predmet: %s)", to_email, subject)
        return True, None
    except SMTPAuthenticationError as exc:
        err = f"SMTP autentifikacija neuspješna: {exc}"
        logger.error(err)
        return False, err
    except SMTPException as exc:
        err = f"SMTP greška: {exc}"
        logger.error(err)
        return False, err
    except OSError as exc:
        err = f"Greška pri spajanju na SMTP ({settings.smtp_host}:{settings.smtp_port}): {exc}"
        logger.error(err)
        return False, err
    except Exception as exc:
        err = f"Neočekivana greška pri slanju emaila: {exc}"
        logger.exception(err)
        return False, err


def notifikacija_status_poslije_slanja(success: bool) -> str:
    if not smtp_configured():
        return "nedostaje_smtp"
    return "poslano" if success else "greska"
