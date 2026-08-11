from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.services.iskoristivost_alerts import (
    filtriraj_opce_iznad_praga,
    obradi_upozorenja_za_opcine,
    provjeri_i_posalji_upozorenja_iskoristivost,
    provjeri_iskoristivost_alert,
)


def test_filtriraj_opce_iznad_praga():
    opce = [
        {"naziv": "Mostar", "postotak_zauzetosti": 95.0, "slobodni": 50, "ukupno": 1000},
        {"naziv": "Travnik", "postotak_zauzetosti": 70.0, "slobodni": 300, "ukupno": 1000},
        {"naziv": "Zenica", "postotak_zauzetosti": 90.0, "slobodni": 100, "ukupno": 1000},
    ]
    result = filtriraj_opce_iznad_praga(opce, 90.0)
    assert len(result) == 2
    assert result[0]["naziv"] == "Mostar"
    assert result[1]["naziv"] == "Zenica"


def test_filtriraj_crnice_91_prolazi():
    opce = [
        {"naziv": "Goražde", "postotak_zauzetosti": 51.0, "slobodni": 6370, "ukupno": 13000},
        {"naziv": "Crnići", "postotak_zauzetosti": 91.0, "slobodni": 90, "ukupno": 1000},
    ]
    result = filtriraj_opce_iznad_praga(opce, 90.0)
    assert len(result) == 1
    assert result[0]["naziv"] == "Crnići"
    assert result[0]["postotak_zauzetosti"] == 91.0


def test_crnice_u_alertu_salje_email(db):
    opce = [
        {"naziv": "Crnići", "postotak_zauzetosti": 91.0, "slobodni": 90, "ukupno": 1000},
    ]
    with (
        patch("app.services.iskoristivost_alerts.smtp_configured", return_value=True),
        patch("app.services.iskoristivost_alerts.posalji_iskoristivost_alert") as mock_posalji,
    ):
        count = obradi_upozorenja_za_opcine(db, opce, "admin@eronet.ba")
    assert count == 1
    mock_posalji.assert_called_once()
    poslane = mock_posalji.call_args[0][2]
    assert poslane[0]["naziv"] == "Crnići"

    db.execute(text("DELETE FROM notifikacije WHERE sadrzaj LIKE '%Crnići%'"))
    db.commit()


def test_provjeri_iskoristivost_alert_vraca_listu(db):
    mock_stats = {
        "po_opcini": [
            {"naziv": "Crnići", "postotak_zauzetosti": 91.0, "slobodni": 90, "ukupno": 1000},
        ],
    }
    with (
        patch("app.services.iskoristivost_alerts.statistike", return_value=mock_stats),
        patch("app.services.iskoristivost_alerts.smtp_configured", return_value=True),
        patch("app.services.iskoristivost_alerts.posalji_iskoristivost_alert"),
    ):
        rez = provjeri_iskoristivost_alert()
    assert rez["poslano_opcina"] == 1
    assert rez["opce"][0]["naziv"] == "Crnići"
    assert rez["prag"] == 90.0

    db.execute(text("DELETE FROM notifikacije WHERE sadrzaj LIKE '%Crnići%'"))
    db.commit()


def test_admin_iskoristivost_provjeri_endpoint(client: TestClient, admin_token: str, db):
    mock_stats = {
        "po_opcini": [
            {"naziv": "Crnići", "postotak_zauzetosti": 91.0, "slobodni": 90, "ukupno": 1000},
        ],
    }
    with (
        patch("app.services.iskoristivost_alerts.statistike", return_value=mock_stats),
        patch("app.services.iskoristivost_alerts.smtp_configured", return_value=True),
        patch("app.services.iskoristivost_alerts.posalji_iskoristivost_alert"),
    ):
        res = client.post(
            "/admin/iskoristivost/provjeri",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["poslano_opcina"] == 1
    assert body["opce"][0]["naziv"] == "Crnići"
    assert body["opce"][0]["postotak_zauzetosti"] == 91.0

    db.execute(text("DELETE FROM notifikacije WHERE sadrzaj LIKE '%Crnići%'"))
    db.commit()


def test_obradi_upozorenja_kreira_notifikacije(db):
    opce = [
        {"naziv": "TestOpcinaAlert", "postotak_zauzetosti": 92.5, "slobodni": 77, "ukupno": 1000},
    ]
    with (
        patch("app.services.iskoristivost_alerts.smtp_configured", return_value=True),
        patch("app.services.iskoristivost_alerts.posalji_iskoristivost_alert"),
    ):
        count = obradi_upozorenja_za_opcine(db, opce, "admin@eronet.ba")
    assert count == 1

    row = db.execute(
        text(
            """
            SELECT predmet, sadrzaj, status, tip
            FROM notifikacije
            WHERE sadrzaj LIKE '%TestOpcinaAlert%'
            ORDER BY id DESC
            LIMIT 1
            """
        )
    ).one()
    assert "TestOpcinaAlert" in row.sadrzaj
    assert "92.5" in row.sadrzaj
    assert "77" in row.sadrzaj
    assert row.tip == "iskoristivost_upozorenje"

    db.execute(
        text("DELETE FROM notifikacije WHERE sadrzaj LIKE '%TestOpcinaAlert%'")
    )
    db.commit()


def test_provjeri_i_posalji_poziva_statistike(db):
    mock_stats = {
        "po_opcini": [
            {"naziv": "VisokaOpcina", "postotak_zauzetosti": 91.0, "slobodni": 9, "ukupno": 100},
        ],
    }
    with (
        patch("app.services.iskoristivost_alerts.statistike", return_value=mock_stats),
        patch(
            "app.services.iskoristivost_alerts.obradi_upozorenja_za_opcine",
            return_value=1,
        ) as mock_obradi,
    ):
        count = provjeri_i_posalji_upozorenja_iskoristivost()
    assert count == 1
    mock_obradi.assert_called_once()
    args = mock_obradi.call_args[0]
    assert args[1][0]["naziv"] == "VisokaOpcina"
