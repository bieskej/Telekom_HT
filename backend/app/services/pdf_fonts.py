"""Registracija DejaVu Sans fontova za PDF (hrvatska latinica s dijakriticima)."""
import logging
import os
from functools import lru_cache
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
FONTS_DIR = BACKEND_ROOT / "assets" / "fonts"

FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
FONT_OBLIQUE = "DejaVuSans-Oblique"

_FONT_FILES = {
    FONT_REGULAR: "DejaVuSans.ttf",
    FONT_BOLD: "DejaVuSans-Bold.ttf",
    FONT_OBLIQUE: "DejaVuSans-Oblique.ttf",
}

_MIN_TTF_BYTES = 100_000


@lru_cache(maxsize=1)
def _register_fonts() -> None:
    for name, filename in _FONT_FILES.items():
        if name in pdfmetrics.getRegisteredFontNames():
            continue
        path = FONTS_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"PDF font nije pronađen: {path}. "
                "Očekivani fontovi: backend/assets/fonts/DejaVuSans*.ttf"
            )
        size = path.stat().st_size
        if size < _MIN_TTF_BYTES:
            raise ValueError(
                f"PDF font {path.name} je neispravan ({size} B). "
                "Ponovno preuzmite DejaVu TTF (vidi backend/assets/fonts/README.md)."
            )
        pdfmetrics.registerFont(TTFont(name, str(path)))


def pdf_set_font(canvas, style: str = "regular", size: int = 11) -> None:
    """Postavi font na canvas (regular | bold | oblique)."""
    _register_fonts()
    if style == "bold":
        canvas.setFont(FONT_BOLD, size)
    elif style == "oblique":
        canvas.setFont(FONT_OBLIQUE, size)
    else:
        canvas.setFont(FONT_REGULAR, size)


def assert_pdf_has_dejavu(pdf_bytes: bytes, label: str = "PDF") -> None:
    """Provjeri da je PDF generiran s DejaVu (ne starim Helvetica cacheom)."""
    if b"DejaVuSans" not in pdf_bytes:
        raise RuntimeError(
            f"{label} nema ugrađeni DejaVuSans font. "
            "Restartajte backend iz c:\\Telekom_HT\\scripts\\start-backend.ps1 (port 8004)."
        )


def init_pdf_fonts() -> dict:
    """Registriraj fontove pri startu aplikacije; vrati dijagnostiku za /health."""
    _register_fonts()
    cwd = Path(os.getcwd()).resolve()
    backend = BACKEND_ROOT.resolve()
    if cwd != backend:
        logger.warning(
            "CWD (%s) nije backend root (%s). Pokrenite: cd backend && uvicorn app.main:app",
            cwd,
            backend,
        )
    registered = [n for n in (FONT_REGULAR, FONT_BOLD, FONT_OBLIQUE) if n in pdfmetrics.getRegisteredFontNames()]
    return {
        "pdf_font": "dejavu",
        "fonts_dir": str(FONTS_DIR),
        "backend_root": str(backend),
        "cwd": str(cwd),
        "cwd_matches_backend": cwd == backend,
        "registered": registered,
    }


def pdf_font_health() -> dict:
    """Status fontova za /health (ne baca iznimku)."""
    try:
        return {**init_pdf_fonts(), "status": "ok"}
    except Exception as exc:
        return {
            "pdf_font": "error",
            "status": "error",
            "detail": str(exc),
            "fonts_dir": str(FONTS_DIR),
            "backend_root": str(BACKEND_ROOT.resolve()),
            "cwd": str(Path(os.getcwd()).resolve()),
        }
