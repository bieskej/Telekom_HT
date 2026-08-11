"""Slanje HTML email obavijesti (dodjela, karantena, digest, iskorištenost)."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.dokumenti_service import osiguraj_dokumente
from app.services.email_service import send_html_email
from app.services.phone import formatiraj_broj

logger = logging.getLogger(__name__)

PREDMET_DODJELA = "HT Eronet — potvrda dodjele broja"
PREDMET_KARANTENA_START = "HT Eronet — broj u karanteni"
PREDMET_KARANTENA_END = "HT Eronet — karantena istekla"
PREDMET_DIGEST = "HT Eronet — tjedni pregled"
PREDMET_ISKORISTIVOST = "Upozorenje: visoka iskorištenost brojeva - HT Eronet"


def posalji_email_dodjela(
    db: Session,
    msisdn_id: int,
    ime: str,
    prezime: str,
    email: str,
    broj_formatiran: str,
    kvaliteta: str,
    adresa: str,
    grad: str,
    postanski_broj: str,
) -> None:
    if not email or not email.strip():
        return
    try:
        ugovor_pdf = osiguraj_dokumente(db, msisdn_id, "ugovor")
        context = {
            "ime": ime,
            "prezime": prezime,
            "broj_formatiran": broj_formatiran,
            "datum": datetime.now().strftime("%d.%m.%Y."),
            "kvaliteta": kvaliteta.capitalize(),
            "adresa": adresa,
            "grad": grad,
            "postanski_broj": postanski_broj,
        }
        send_html_email(
            email.strip(),
            PREDMET_DODJELA,
            "dodjela.html",
            context,
            pdf_bytes=ugovor_pdf,
            filename=f"ugovor_{msisdn_id}.pdf",
            msisdn_id=msisdn_id,
            db=db,
        )
    except Exception:
        logger.exception("Greška slanja dodjela emaila za msisdn %s", msisdn_id)


def posalji_email_karantena_start(
    db: Session,
    msisdn_id: int,
    email: str | None,
    ime: str | None,
    prezime: str | None,
    broj: str,
    datum_karantene,
    karantena_dana: int,
) -> None:
    if not email or not email.strip():
        return
    istek = datum_karantene + timedelta(days=karantena_dana)
    if hasattr(istek, "strftime"):
        datum_isteka = istek.strftime("%d.%m.%Y.")
    else:
        datum_isteka = str(istek)
    context = {
        "ime": ime or "",
        "prezime": prezime or "",
        "broj_formatiran": formatiraj_broj(broj),
        "datum_isteka": datum_isteka,
        "karantena_dana": karantena_dana,
    }
    send_html_email(
        email.strip(),
        PREDMET_KARANTENA_START,
        "karantena_start.html",
        context,
        msisdn_id=msisdn_id,
        db=db,
    )


def posalji_email_karantena_end(
    db: Session,
    msisdn_id: int,
    email: str | None,
    ime: str | None,
    prezime: str | None,
    broj: str,
) -> None:
    if not email or not email.strip():
        return
    context = {
        "ime": ime or "",
        "prezime": prezime or "",
        "broj_formatiran": formatiraj_broj(broj),
    }
    send_html_email(
        email.strip(),
        PREDMET_KARANTENA_END,
        "karantena_end.html",
        context,
        msisdn_id=msisdn_id,
        db=db,
    )


def posalji_digest_admin(db: Session) -> bool:
    """Tjedni digest na admin_alert_email."""
    sada = datetime.now(timezone.utc)
    od = sada - timedelta(days=7)

    ukupno = db.execute(
        text(
            """
            SELECT COUNT(*)::int FROM msisdn_history
            WHERE akcija = 'dodjela' AND promijenjeno_at >= :od
            """
        ),
        {"od": od},
    ).scalar() or 0

    top_opcine = db.execute(
        text(
            """
            SELECT o.naziv, COUNT(h.id)::int AS broj
            FROM msisdn_history h
            JOIN msisdn m ON m.id = h.msisdn_id
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE h.akcija = 'dodjela' AND h.promijenjeno_at >= :od
            GROUP BY o.naziv
            ORDER BY broj DESC
            LIMIT 5
            """
        ),
        {"od": od},
    ).fetchall()

    top_radnici = db.execute(
        text(
            """
            SELECT COALESCE(rad.ime || ' ' || rad.prezime, 'Sustav') AS ime, COUNT(h.id)::int AS broj
            FROM msisdn_history h
            LEFT JOIN radnici rad ON rad.id = h.radnik_id
            WHERE h.akcija = 'dodjela' AND h.promijenjeno_at >= :od
            GROUP BY rad.ime, rad.prezime
            ORDER BY broj DESC
            LIMIT 5
            """
        ),
        {"od": od},
    ).fetchall()

    po_danima = db.execute(
        text(
            """
            SELECT to_char(promijenjeno_at::date, 'DD.MM.YYYY.') AS datum,
                   COUNT(*)::int AS broj
            FROM msisdn_history
            WHERE akcija = 'dodjela' AND promijenjeno_at >= :od
            GROUP BY promijenjeno_at::date
            ORDER BY promijenjeno_at::date DESC
            """
        ),
        {"od": od},
    ).fetchall()

    context = {
        "razdoblje": f"{od.strftime('%d.%m.%Y.')} – {sada.strftime('%d.%m.%Y.')}",
        "ukupno_dodjela": ukupno,
        "top_opcine": [{"naziv": r.naziv, "broj": r.broj} for r in top_opcine],
        "top_radnici": [{"ime": r.ime, "broj": r.broj} for r in top_radnici],
        "po_danima": [{"datum": r.datum, "broj": r.broj} for r in po_danima],
    }
    ok, _, _ = send_html_email(
        settings.admin_alert_email,
        PREDMET_DIGEST,
        "digest_admin.html",
        context,
        db=db,
    )
    return ok


def posalji_iskoristivost_alert(
    db: Session,
    admin_email: str,
    top_opcine: list[dict],
    prag: float,
) -> None:
    """Top 5 općina iznad praga."""
    sortirano = sorted(top_opcine, key=lambda x: x.get("postotak_zauzetosti", 0), reverse=True)[:5]
    context = {
        "prag": int(prag),
        "top_opcine": [
            {
                "naziv": o["naziv"],
                "postotak": round(float(o.get("postotak_zauzetosti", 0)), 1),
                "slobodni": o.get("slobodni", 0),
                "ukupno": o.get("ukupno", 0),
            }
            for o in sortirano
        ],
    }
    send_html_email(
        admin_email,
        PREDMET_ISKORISTIVOST,
        "iskoristivost_alert.html",
        context,
        db=db,
    )


def obradi_dodjelu_email_html(
    msisdn_id: int,
    ime: str,
    prezime: str,
    email: str,
    broj_formatiran: str,
    kvaliteta_naziv: str,
    adresa: str = "",
    grad: str = "",
    postanski_broj: str = "",
) -> None:
    """Background task zamjena za stari invoice_email flow."""
    db = SessionLocal()
    try:
        posalji_email_dodjela(
            db,
            msisdn_id,
            ime,
            prezime,
            email,
            broj_formatiran,
            kvaliteta_naziv,
            adresa,
            grad,
            postanski_broj,
        )
    except Exception:
        logger.exception("Background dodjela email failed msisdn=%s", msisdn_id)
    finally:
        db.close()


def ponovi_email_iz_loga(db: Session, log_id: int) -> tuple[bool, str | None, int | None]:
    row = db.execute(
        text(
            "SELECT id, primatelj, predmet, html_tijelo, msisdn_id FROM email_log WHERE id = :id"
        ),
        {"id": log_id},
    ).fetchone()
    if not row:
        return False, "Log nije pronađen.", None
    if not row.html_tijelo:
        return False, "Log nema spremljenog HTML sadržaja.", None
    return send_html_email(
        row.primatelj,
        row.predmet,
        html_body=row.html_tijelo,
        msisdn_id=row.msisdn_id,
        db=db,
    )
