import io
import json
from datetime import datetime

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.services.pdf_fonts import pdf_set_font


def generiraj_pdf_ugovor(
    *,
    ime: str,
    prezime: str,
    jmbg: str,
    adresa: str,
    grad: str,
    postanski_broj: str,
    broj_formatiran: str,
    kvaliteta_naziv: str,
    cijena: float,
    msisdn_id: int | None = None,
    portal_base_url: str = "http://localhost:5173",
) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    danas = datetime.now().strftime("%d.%m.%Y.")

    c.setFillColor(colors.HexColor("#0054A6"))
    c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    pdf_set_font(c, "bold", 16)
    c.drawString(2 * cm, height - 1.6 * cm, "HT Eronet d.o.o.")

    if msisdn_id is not None:
        qr_payload = json.dumps(
            {"portal": f"{portal_base_url.rstrip('/')}/portal/moji-brojevi", "msisdn_id": msisdn_id},
            ensure_ascii=False,
        )
        qr_img = qrcode.make(qr_payload)
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        from reportlab.lib.utils import ImageReader

        qr_size = 2.2 * cm
        c.drawImage(
            ImageReader(qr_buf),
            width - qr_size - 1.5 * cm,
            height - qr_size - 1.2 * cm,
            qr_size,
            qr_size,
            mask="auto",
        )
        pdf_set_font(c, "regular", 7)
        c.setFillColor(colors.white)
        c.drawRightString(width - 1.5 * cm, height - qr_size - 1.4 * cm, "Portal kupca")

    y = height - 4 * cm
    c.setFillColor(colors.black)
    pdf_set_font(c, "bold", 14)
    c.drawCentredString(width / 2, y, "UGOVOR O DODJELI BROJA")
    y -= 1.2 * cm

    pdf_set_font(c, "regular", 11)
    for line in [
        f"Datum: {danas}",
        f"Mjesto: {grad}",
        "",
        "Podaci korisnika:",
        f"  Ime i prezime: {ime} {prezime}",
        f"  JMBG: {jmbg}",
        f"  Adresa: {adresa}",
        f"  Grad: {grad}",
        f"  Poštanski broj: {postanski_broj}",
        "",
        f"Dodijeljeni broj: {broj_formatiran}",
        f"Kvaliteta usluge: {kvaliteta_naziv.capitalize()}",
        f"Mjesečna cijena (bez PDV): {float(cijena):.2f} KM",
        "",
        "Članak 1.",
        "Operater HT Eronet d.o.o. dodjeljuje korisniku gore navedeni telefonski broj",
        "u skladu s važećim pravilima i tarifama za odabranu kvalitetu usluge.",
        "",
        "Članak 2.",
        "Korisnik se obvezuje koristiti broj u skladu s zakonom i općim uvjetima poslovanja.",
    ]:
        c.drawString(2 * cm, y, line)
        y -= 0.5 * cm
        if y < 5 * cm:
            c.showPage()
            y = height - 2 * cm

    y -= 0.5 * cm
    c.drawString(2 * cm, y, "Potpis ovlaštene osobe: _________________________")
    y -= 1 * cm
    c.drawString(2 * cm, y, "Potpis korisnika: _________________________")
    y -= 1.2 * cm
    pdf_set_font(c, "oblique", 9)
    c.drawString(
        2 * cm,
        y,
        "Ovaj ugovor je generiran elektroničkim putem i ne zahtijeva fizički potpis.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
