from pathlib import Path

import pytest
from sqlalchemy import text

from app.services.postanski_import import import_postanski_uredi, parse_postanski_uredi

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "postanski_sample.csv"


def test_parse_csv_fixture():
    rows = parse_postanski_uredi(FIXTURE)
    assert len(rows) == 5
    assert rows[0] == ("88360", "Stolac", "HP")


def test_import_postanski_sample(db):
    result = import_postanski_uredi(db, FIXTURE)
    assert result["ukupno"] == 5
    assert result["novi"] + result["azurirani"] + result["preskoceni"] == 5
    assert result["novi"] + result["azurirani"] >= 1, result

    stolac = db.execute(
        text(
            """
            SELECT l.postanski_broj, l.posta_operater, o.naziv, z.oznaka
            FROM lokacije l
            JOIN opcine o ON o.id = l.opcina_id
            JOIN zupanije z ON z.id = o.zupanija_id
            WHERE l.postanski_broj = '88360'
            """
        )
    ).fetchone()
    assert stolac is not None
    assert stolac.posta_operater == "HP"
    assert stolac.naziv == "Stolac"
    assert stolac.oznaka == "HNŽ"

    crnici = db.execute(
        text(
            """
            SELECT o.naziv FROM lokacije l
            JOIN opcine o ON o.id = l.opcina_id
            WHERE l.postanski_broj = '88367'
            """
        )
    ).scalar()
    assert crnici == "Crnići"

    brcko = db.execute(
        text("SELECT entitet FROM opcine o JOIN lokacije l ON l.opcina_id = o.id WHERE l.postanski_broj = '76120'")
    ).scalar()
    assert brcko == "Brčko"


@pytest.mark.skipif(not Path(__file__).resolve().parents[2].parent.joinpath("popis_ureda.pdf").is_file(), reason="PDF nije u repou")
def test_import_full_pdf(db):
    pdf = Path(__file__).resolve().parents[2].parent / "popis_ureda.pdf"
    result = import_postanski_uredi(db, pdf)
    assert result["ukupno"] > 400
    count = db.execute(text("SELECT COUNT(*) FROM lokacije WHERE tip = 'postanski_ured'")).scalar()
    assert count >= result["novi"]
