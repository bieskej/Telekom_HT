import io

import logging

from datetime import datetime



from reportlab.lib import colors

from reportlab.lib.pagesizes import A4

from reportlab.lib.units import cm

from reportlab.pdfgen import canvas

from sqlalchemy import text

from sqlalchemy.orm import Session



from app.config import settings

from app.database import SessionLocal

from app.services.email_service import (

    notifikacija_status_poslije_slanja,

    send_email_with_attachment,

    smtp_configured,

)

from app.services.pdf_fonts import pdf_set_font
from app.services.pdf_potpis import crtaj_potpis_desno



logger = logging.getLogger(__name__)



PDV_STOPA = 0.17





def generiraj_pdf_racun(
    ime: str,
    prezime: str,
    jmbg: str,
    email: str,
    broj_formatiran: str,
    kvaliteta_naziv: str,
    cijena: float,
    *,
    adresa: str = "",
    grad: str = "",
    postanski_broj: str = "",
) -> bytes:

    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4



    c.setFillColor(colors.HexColor("#0054A6"))

    c.rect(0, height - 3 * cm, width, 3 * cm, fill=1, stroke=0)

    c.setFillColor(colors.white)

    pdf_set_font(c, "bold", 20)

    c.drawString(2 * cm, height - 2 * cm, "HT Eronet")

    pdf_set_font(c, "regular", 10)

    c.drawString(2 * cm, height - 2.6 * cm, "Račun za dodjelu telefonskog broja")



    y = height - 4.5 * cm

    c.setFillColor(colors.black)

    pdf_set_font(c, "bold", 12)

    c.drawString(2 * cm, y, "Podaci korisnika")

    y -= 0.7 * cm

    pdf_set_font(c, "regular", 11)

    for line in [
        f"Ime i prezime: {ime} {prezime}",
        f"JMBG: {jmbg}",
        f"Email: {email}",
        f"Adresa: {adresa}",
        f"Grad: {grad}",
        f"Poštanski broj: {postanski_broj}",
        f"Dodijeljeni broj: {broj_formatiran}",
        f"Kvaliteta: {kvaliteta_naziv.capitalize()}",
        f"Datum: {datetime.now().strftime('%d.%m.%Y.')}",
    ]:

        c.drawString(2 * cm, y, line)

        y -= 0.55 * cm



    osnovica = float(cijena)

    pdv = round(osnovica * PDV_STOPA, 2)

    ukupno = round(osnovica + pdv, 2)



    y -= 0.5 * cm

    pdf_set_font(c, "bold", 12)

    c.drawString(2 * cm, y, "Naplata")

    y -= 0.7 * cm

    pdf_set_font(c, "regular", 11)

    for line in [

        f"Osnovica: {osnovica:.2f} KM",

        f"PDV (17%): {pdv:.2f} KM",

        f"Ukupno za naplatu: {ukupno:.2f} KM",

    ]:

        c.drawString(2 * cm, y, line)

        y -= 0.55 * cm



    crtaj_potpis_desno(c, width, y)



    c.showPage()

    c.save()

    buffer.seek(0)

    return buffer.read()





def generiraj_pdf_racun_bulk(

    ime: str,

    prezime: str,

    jmbg: str,

    email: str,

    brojevi_formatirani: list[str],

    kvaliteta_naziv: str,

    cijena_po_komadu: float,

    komada: int,

) -> bytes:

    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4



    c.setFillColor(colors.HexColor("#0054A6"))

    c.rect(0, height - 3 * cm, width, 3 * cm, fill=1, stroke=0)

    c.setFillColor(colors.white)

    pdf_set_font(c, "bold", 20)

    c.drawString(2 * cm, height - 2 * cm, "HT Eronet")

    pdf_set_font(c, "regular", 10)

    c.drawString(2 * cm, height - 2.6 * cm, "Račun za bulk dodjelu telefonskih brojeva")



    y = height - 4.5 * cm

    c.setFillColor(colors.black)

    pdf_set_font(c, "bold", 12)

    c.drawString(2 * cm, y, "Podaci korisnika")

    y -= 0.7 * cm

    pdf_set_font(c, "regular", 11)

    for line in [

        f"Ime i prezime: {ime} {prezime}",

        f"JMBG: {jmbg}",

        f"Email: {email}",

        f"Kvaliteta: {kvaliteta_naziv.capitalize()}",

        f"Broj dodijeljenih komada: {komada}",

        f"Datum: {datetime.now().strftime('%d.%m.%Y.')}",

    ]:

        c.drawString(2 * cm, y, line)

        y -= 0.55 * cm



    y -= 0.3 * cm

    pdf_set_font(c, "bold", 12)

    c.drawString(2 * cm, y, "Dodijeljeni brojevi")

    y -= 0.6 * cm

    pdf_set_font(c, "regular", 10)

    prikaz = brojevi_formatirani[:15]

    for broj in prikaz:

        c.drawString(2 * cm, y, f"• {broj}")

        y -= 0.45 * cm

    if len(brojevi_formatirani) > 15:

        c.drawString(2 * cm, y, f"... i još {len(brojevi_formatirani) - 15} brojeva")

        y -= 0.45 * cm



    osnovica = round(float(cijena_po_komadu) * komada, 2)

    pdv = round(osnovica * PDV_STOPA, 2)

    ukupno = round(osnovica + pdv, 2)



    y -= 0.5 * cm

    pdf_set_font(c, "bold", 12)

    c.drawString(2 * cm, y, "Naplata")

    y -= 0.7 * cm

    pdf_set_font(c, "regular", 11)

    for line in [

        f"Cijena po komadu: {cijena_po_komadu:.2f} KM",

        f"Osnovica ({komada} × {cijena_po_komadu:.2f} KM): {osnovica:.2f} KM",

        f"PDV (17%): {pdv:.2f} KM",

        f"Ukupno za naplatu: {ukupno:.2f} KM",

    ]:

        c.drawString(2 * cm, y, line)

        y -= 0.55 * cm



    crtaj_potpis_desno(c, width, y)



    c.showPage()

    c.save()

    buffer.seek(0)

    return buffer.read()





def posalji_email_s_racunom(
    email_primatelj: str,
    pdf_bytes: bytes,
    broj_formatiran: str,
    *,
    predmet: str | None = None,
    poruka: str | None = None,
    naziv_datoteke: str = "racun_eronet.pdf",
    nacin_placanja: str | None = None,
) -> tuple[bool, str | None]:

    return send_email_with_attachment(

        email_primatelj,

        predmet or "Potvrda dodjele broja - HT Eronet",

        poruka
        or (
            f"Poštovani,\n\npotvrđujemo dodjelu broja {broj_formatiran}.\n"
            f"U privitku se nalazi račun (ugovor preuzmite u aplikaciji).\n"
            + (
                f"Plaćeno {'karticom' if nacin_placanja == 'kartica' else 'gotovinom'}.\n\n"
                if nacin_placanja
                else "\n"
            )
            + "Srdačan pozdrav,\nHT Eronet"
        ),

        pdf_bytes,

        naziv_datoteke,

    )





def _zapisi_notifikaciju(

    db: Session,

    email: str,

    msisdn_id: int,

    poslano: bool | None,

    sadrzaj: str,

    tip: str = "email_potvrda",

) -> None:

    if poslano is None:

        status = "nedostaje_smtp"

    else:

        status = notifikacija_status_poslije_slanja(poslano)



    db.execute(

        text(

            """

            INSERT INTO notifikacije (email_primatelj, predmet, sadrzaj, status, msisdn_id, poslano_at, tip)

            VALUES (:email, :predmet, :sadrzaj, :status, :msisdn_id,

                    CASE WHEN :status = 'poslano' THEN NOW() ELSE NULL END, :tip)

            """

        ),

        {

            "email": email,

            "predmet": "Potvrda dodjele broja - HT Eronet",

            "sadrzaj": sadrzaj,

            "status": status,

            "msisdn_id": msisdn_id,

            "tip": tip,

        },

    )

    db.commit()





def obradi_bulk_dodjelu_email(

    msisdn_id: int,

    ime: str,

    prezime: str,

    jmbg: str,

    email: str,

    brojevi_formatirani: list[str],

    kvaliteta_naziv: str,

    cijena_po_komadu: float,

    komada: int,

) -> None:

    db = SessionLocal()

    try:

        pdf = generiraj_pdf_racun_bulk(

            ime,

            prezime,

            jmbg,

            email,

            brojevi_formatirani,

            kvaliteta_naziv,

            cijena_po_komadu,

            komada,

        )

        sazetak = f"{komada} brojeva ({kvaliteta_naziv})"

        if smtp_configured():

            ok, err = posalji_email_s_racunom(

                email,

                pdf,

                sazetak,

                predmet="Potvrda bulk dodjele brojeva - HT Eronet",

                poruka=(

                    f"Poštovani,\n\npotvrđujemo bulk dodjelu {komada} brojeva "

                    f"(kvaliteta: {kvaliteta_naziv.capitalize()}).\n"

                    f"U privitku se nalazi zajednički račun.\n\nSrdačan pozdrav,\nHT Eronet"

                ),

                naziv_datoteke="racun_bulk_eronet.pdf",

            )

            _zapisi_notifikaciju(

                db,

                email,

                msisdn_id,

                ok,

                f"Bulk dodjela {komada} brojeva ({kvaliteta_naziv})" + (f" | {err}" if err else ""),

            )

        else:

            _zapisi_notifikaciju(

                db,

                email,

                msisdn_id,

                None,

                f"Bulk dodjela {komada} brojeva ({kvaliteta_naziv}) – SMTP nije konfiguriran",

            )

    except Exception as exc:

        logger.exception("Background bulk email task failed: %s", exc)

        try:

            _zapisi_notifikaciju(db, email, msisdn_id, False, str(exc))

        except Exception:

            pass

    finally:

        db.close()





def obradi_dodjelu_email(
    msisdn_id: int,
    ime: str,
    prezime: str,
    jmbg: str,
    email: str,
    broj: str,
    broj_formatiran: str,
    kvaliteta_naziv: str,
    cijena: float,
    *,
    adresa: str = "",
    grad: str = "",
    postanski_broj: str = "",
    nacin_placanja: str | None = None,
) -> None:

    db = SessionLocal()

    try:

        pdf = generiraj_pdf_racun(
            ime,
            prezime,
            jmbg,
            email,
            broj_formatiran,
            kvaliteta_naziv,
            cijena,
            adresa=adresa,
            grad=grad,
            postanski_broj=postanski_broj,
        )

        if smtp_configured():

            ok, err = posalji_email_s_racunom(
                email, pdf, broj_formatiran, nacin_placanja=nacin_placanja
            )

            _zapisi_notifikaciju(

                db,

                email,

                msisdn_id,

                ok,

                f"Dodjela broja {broj_formatiran} ({kvaliteta_naziv})" + (f" | {err}" if err else ""),

            )

        else:

            _zapisi_notifikaciju(

                db,

                email,

                msisdn_id,

                None,

                f"Dodjela broja {broj_formatiran} ({kvaliteta_naziv}) – SMTP nije konfiguriran",

            )

    except Exception as exc:

        logger.exception("Background email task failed: %s", exc)

        try:

            _zapisi_notifikaciju(db, email, msisdn_id, False, str(exc))

        except Exception:

            pass

    finally:

        db.close()





def ponovi_neuspjele_emailove() -> int:

    if not smtp_configured():

        return 0



    db = SessionLocal()

    count = 0

    try:

        rows = db.execute(

            text(

                """

                SELECT n.id, n.email_primatelj, m.id AS msisdn_id, m.broj, m.ime, m.prezime,

                       m.jmbg, m.email, k.naziv AS kvaliteta, k.cijena

                FROM notifikacije n

                JOIN msisdn m ON m.id = n.msisdn_id

                LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id

                WHERE n.status IN ('greska', 'ceka', 'nedostaje_smtp') AND n.tip = 'email_potvrda'

                LIMIT 20

                """

            )

        ).fetchall()

        for r in rows:

            broj_fmt = __import__("app.services.phone", fromlist=["formatiraj_broj"]).formatiraj_broj(r.broj)

            pdf = generiraj_pdf_racun(

                r.ime or "",

                r.prezime or "",

                r.jmbg or "",

                r.email or r.email_primatelj,

                broj_fmt,

                r.kvaliteta or "silver",

                float(r.cijena or 10),

            )

            ok, _ = posalji_email_s_racunom(r.email_primatelj, pdf, broj_fmt)

            if ok:

                db.execute(

                    text("UPDATE notifikacije SET status='poslano', poslano_at=NOW() WHERE id=:id"),

                    {"id": r.id},

                )

                count += 1

        db.commit()

    finally:

        db.close()

    return count


