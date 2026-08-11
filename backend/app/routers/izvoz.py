import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled
from app.database import get_db
from app.services import msisdn_service

router = APIRouter(prefix="/izvoz", tags=["izvoz"])


@router.get("/statistike/excel")
async def izvoz_statistike_excel(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    data = msisdn_service.statistike(db)
    wb = Workbook()
    ws = wb.active
    ws.title = "Statistika"
    ws.append(["Metrika", "Vrijednost"])
    ws.append(["Ukupno", data["ukupno"]])
    ws.append(["Slobodni", data["slobodni"]])
    ws.append(["Zauzeti", data["zauzeti"]])
    ws.append(["Karantena", data["karantena"]])
    ws.append(["Iskoristivost %", data["iskoristivost"]])
    ws.append([])
    ws.append(["Općina", "Ukupno", "Slobodni", "Zauzetost %"])
    for o in data["po_opcini"]:
        ws.append([o["naziv"], o["ukupno"], o["slobodni"], o["postotak_zauzetosti"]])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"statistika_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/statistike/pdf")
async def izvoz_statistike_pdf(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    data = msisdn_service.statistike(db)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "HT Eronet – Statistika")
    y -= 40
    c.setFont("Helvetica", 11)
    for line in [
        f"Ukupno: {data['ukupno']}",
        f"Slobodni: {data['slobodni']}",
        f"Zauzeti: {data['zauzeti']}",
        f"Karantena: {data['karantena']}",
        f"Iskoristivost: {data['iskoristivost']}%",
    ]:
        c.drawString(50, y, line)
        y -= 22
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Po općinama")
    y -= 25
    c.setFont("Helvetica", 10)
    for o in data["po_opcini"][:25]:
        c.drawString(50, y, f"{o['naziv']}: {o['postotak_zauzetosti']}% ({o['slobodni']} slobodnih)")
        y -= 18
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    buf.seek(0)
    filename = f"statistika_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
