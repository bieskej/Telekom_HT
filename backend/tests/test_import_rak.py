import io

import pytest
from openpyxl import Workbook
from sqlalchemy import text

from app.services.rak_import import import_rak_datoteka


def _make_rak_xlsx(ndc: str = "36", blok: str = "9998", operator: str = "HT d.d. Mostar") -> bytes:
    wb = Workbook()
    ws = wb.active
    for _ in range(6):
        ws.append([None, None, None, None, None, None])
    ws.append(["NDC", "Blok", "Duzina", None, "Operator", None])
    ws.append([ndc, blok, 8, None, operator, None])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def admin_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela")
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_import_rak_valid(client, db, admin_headers):
    unique_blok = "9991"
    db.execute(
        text(
            """
            DELETE FROM msisdn WHERE broj LIKE :p;
            DELETE FROM rasponi WHERE pocetak LIKE :p;
            """
        ),
        {"p": f"36{unique_blok}%"},
    )
    db.commit()
    xlsx = _make_rak_xlsx(blok=unique_blok)
    res = client.post(
        "/admin/import-rak",
        headers=admin_headers,
        files={"datoteka": (f"test_{unique_blok}.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["novi_rasponi"] >= 1
    assert data["novi_brojevi"] == 100
    assert data["preskoceni"] == 0

    db.execute(
        text(
            """
            DELETE FROM msisdn WHERE broj LIKE :pattern;
            DELETE FROM rasponi WHERE pocetak LIKE :pattern;
            """
        ),
        {"pattern": f"36{unique_blok}%"},
    )
    db.commit()


def test_import_rak_duplicate(client, db, admin_headers):
    unique_blok = "9992"
    db.execute(
        text("DELETE FROM msisdn WHERE broj LIKE :p; DELETE FROM rasponi WHERE pocetak LIKE :p;"),
        {"p": f"36{unique_blok}%"},
    )
    db.commit()
    xlsx = _make_rak_xlsx(blok=unique_blok)

    first = client.post(
        "/admin/import-rak",
        headers=admin_headers,
        files={"datoteka": (f"dup_{unique_blok}.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert first.status_code == 200

    second = client.post(
        "/admin/import-rak",
        headers=admin_headers,
        files={"datoteka": (f"dup_{unique_blok}.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert second.status_code == 200
    data = second.json()
    assert data["novi_brojevi"] == 0
    assert data["preskoceni"] == 100

    db.execute(
        text("DELETE FROM msisdn WHERE broj LIKE :p; DELETE FROM rasponi WHERE pocetak LIKE :p;"),
        {"p": f"36{unique_blok}%"},
    )
    db.commit()


def test_import_rak_service_unit(db):
    blok = "9993"
    db.execute(
        text("DELETE FROM msisdn WHERE broj LIKE :p; DELETE FROM rasponi WHERE pocetak LIKE :p;"),
        {"p": f"36{blok}%"},
    )
    db.commit()
    xlsx = _make_rak_xlsx(blok=blok)
    buf = io.BytesIO(xlsx)
    result = import_rak_datoteka(buf, "unit.xlsx", db)
    assert result["novi_brojevi"] == 100
    db.execute(text("DELETE FROM msisdn WHERE broj LIKE :p"), {"p": f"36{blok}%"})
    db.commit()
