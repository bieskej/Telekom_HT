"""PDF generiranje s hrvatskim dijakriticima (DejaVu Sans)."""
import io

import pytest
from pypdf import PdfReader

from app.services.contract_pdf import generiraj_pdf_ugovor
from app.services.invoice_email import generiraj_pdf_racun


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_racun_hrvatski_znakovi_i_dejavu_font():
    pdf = generiraj_pdf_racun(
        ime="Ivo",
        prezime="Čović",
        jmbg="1501987654321",
        email="ivo.covic@example.com",
        broj_formatiran="+387 61 123 456",
        kvaliteta_naziv="gold",
        cijena=25.0,
        adresa="Ulica šetalište 5",
        grad="Mostar",
        postanski_broj="88000",
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
    assert b"DejaVuSans" in pdf

    text = _pdf_text(pdf)
    assert "Čović" in text
    assert "Račun" in text
    assert "Poštanski" in text
    assert "šetalište" in text
    assert "Mostar" in text


def test_ugovor_hrvatski_znakovi_i_dejavu_font():
    pdf = generiraj_pdf_ugovor(
        ime="Ana",
        prezime="Džafić",
        jmbg="1501987654321",
        adresa="Trg bana Jelačića 1",
        grad="Mostar",
        postanski_broj="88000",
        broj_formatiran="+387 61 999 888",
        kvaliteta_naziv="platinum",
        cijena=50.0,
    )
    assert pdf.startswith(b"%PDF")
    assert b"DejaVuSans" in pdf

    text = _pdf_text(pdf)
    assert "Džafić" in text
    assert "Poštanski" in text
    assert "Članak" in text
    assert "važećim" in text
    assert "UGOVOR" in text
