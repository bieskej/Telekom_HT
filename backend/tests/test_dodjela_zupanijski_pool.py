"""Test županijskog fallbacka u _find_slobodan_ids (HNŽ).

Korisnik iz Stolca mora dobiti broj (lokalno ili iz HNŽ poola).
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from app.services.msisdn_service import _find_slobodan_ids


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela.")
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_stolac_ima_slobodne_brojeve(db):
    rows = _find_slobodan_ids(db, "Stolac", 5)
    assert len(rows) > 0, "Stolac nakon seed-a mora imati slobodne brojeve."


def test_capljina_ima_slobodne_brojeve(db):
    rows = _find_slobodan_ids(db, "Čapljina", 5)
    assert len(rows) > 0


def test_zupanijski_fallback_hnz(db):
    """Kada općina nema brojeva, mora dohvatiti iz iste županije."""
    db.execute(
        text(
            """
            INSERT INTO opcine (naziv, zupanija_id, entitet)
            SELECT 'TestOpcinaPraznaHNZ',
                   (SELECT id FROM zupanije WHERE oznaka = 'HNŽ'),
                   'FBiH'
            ON CONFLICT (naziv, zupanija_id) DO NOTHING
            """
        )
    )
    db.commit()
    try:
        rows = _find_slobodan_ids(db, "TestOpcinaPraznaHNZ", 1)
        assert len(rows) == 1, "Fallback po HNŽ mora vratiti broj iz Mostara/Čapljine/Stolca."
    finally:
        db.execute(text("DELETE FROM opcine WHERE naziv = 'TestOpcinaPraznaHNZ'"))
        db.commit()


def test_pretraga_msisdn_capljina_endpoint(client, auth_headers):
    res = client.get(
        "/msisdn/pretraga",
        params={"opcina_naziv": "Čapljina", "per_page": 5, "page": 1},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ukupno"] > 0, "Čapljina mora imati brojeve u API odgovoru."


def test_pretraga_msisdn_stolac_endpoint(client, auth_headers):
    res = client.get(
        "/msisdn/pretraga",
        params={"opcina_naziv": "Stolac", "per_page": 5, "page": 1},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["ukupno"] > 0
