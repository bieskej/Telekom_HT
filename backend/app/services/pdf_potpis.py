"""Pomoćne funkcije za crtanje digitalnog potpisa na PDF računima (canvas API)."""
from pathlib import Path

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from app.services.pdf_fonts import pdf_set_font

POTPIS_PATH = Path(__file__).resolve().parents[2] / "assets" / "potpis.png"

POTPIS_SIRINA = 4.5 * cm
POTPIS_VISINA = 1.6 * cm
MARGINA = 2 * cm


def crtaj_potpis_desno(c: Canvas, page_width: float, y_iznad_naplata: float) -> None:
    """
    Crta potpis desno, iznad linije naplate (y_iznad_naplata = y koordinata nakon sekcije Naplata).
    """
    x = page_width - POTPIS_SIRINA - MARGINA
    y = max(MARGINA, y_iznad_naplata - POTPIS_VISINA - 0.4 * cm)

    if POTPIS_PATH.exists():
        try:
            img = ImageReader(str(POTPIS_PATH))
            c.drawImage(
                img,
                x,
                y,
                width=POTPIS_SIRINA,
                height=POTPIS_VISINA,
                preserveAspectRatio=True,
                mask="auto",
            )
            return
        except Exception:
            pass

    pdf_set_font(c, "oblique", 9)
    c.drawRightString(
        page_width - MARGINA,
        y + POTPIS_VISINA * 0.4,
        "Digitalno potpisano (slika nije dostupna)",
    )
