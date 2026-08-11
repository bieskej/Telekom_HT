"""Pretraga MSISDN po općini – samo općine s brojevima u RAK lancu."""

import pytest
from sqlalchemy import text


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela – pokreni migrate_auth.sql")
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_opcine_samo_s_brojevima_mostar_u_listi(client, db, auth_headers):
    res = client.get("/opcine", params={"samo_s_brojevima": True}, headers=auth_headers)
    assert res.status_code == 200
    nazivi = {o["naziv"] for o in res.json()}
    assert "Mostar" in nazivi
    mostar = next(o for o in res.json() if o["naziv"] == "Mostar")
    assert mostar["broj_msisdn"] > 0


def test_pretraga_po_opcina_id_mostar_vraca_rezultate(client, db, auth_headers):
    mostar = db.execute(
        text(
            """
            SELECT o.id, COUNT(m.id)::int AS cnt
            FROM opcine o
            JOIN lokacije l ON l.opcina_id = o.id
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            WHERE o.naziv = 'Mostar'
            GROUP BY o.id
            ORDER BY COUNT(m.id) DESC
            LIMIT 1
            """
        )
    ).fetchone()
    if not mostar or mostar.cnt == 0:
        pytest.skip("Nema MSISDN vezanih uz Mostar u test bazi.")

    res = client.get(
        "/msisdn/pretraga",
        params={"opcina_id": mostar.id, "per_page": 5, "page": 1},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ukupno"] > 0
    assert len(body["rezultati"]) > 0
    for item in body["rezultati"]:
        assert item.get("opcina_naziv") == "Mostar"


def test_pretraga_po_opcina_naziv_mostar_partial(client, db, auth_headers):
    """Djelomičan ILIKE filter (ručna pretraga u UI)."""
    res = client.get(
        "/msisdn/pretraga",
        params={"opcina_naziv": "Most", "per_page": 5, "page": 1},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ukupno"] > 0
    for item in body["rezultati"]:
        assert "most" in (item.get("opcina_naziv") or "").lower()


def test_pretraga_po_opcina_naziv_mostar_tocno(client, db, auth_headers):
    """Točan naziv (klik s karte) — samo ta općina."""
    res = client.get(
        "/msisdn/pretraga",
        params={
            "opcina_naziv": "Mostar",
            "opcina_naziv_tocno": True,
            "per_page": 5,
            "page": 1,
        },
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ukupno"] > 0
    for item in body["rezultati"]:
        assert item.get("opcina_naziv") == "Mostar"


def test_opcine_sve_ukljucuju_nulu(client, auth_headers):
    res = client.get("/opcine", headers=auth_headers)
    assert res.status_code == 200
    nule = [o for o in res.json() if o.get("broj_msisdn") == 0]
    assert len(nule) > 0


def test_opcine_pretraga_naziv(client, auth_headers):
    res = client.get(
        "/opcine",
        params={"samo_s_brojevima": True, "pretraga": "most"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert all("most" in o["naziv"].lower() for o in res.json())


def test_dijagnostika_top_opcina_po_msisdn(db):
    """Top općine po broju MSISDN – dokumentacija u test outputu."""
    rows = db.execute(
        text(
            """
            SELECT o.naziv, o.id, COUNT(m.id)::int AS broj
            FROM opcine o
            JOIN lokacije l ON l.opcina_id = o.id
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            GROUP BY o.naziv, o.id
            ORDER BY broj DESC
            LIMIT 10
            """
        )
    ).fetchall()
    if not rows:
        pytest.skip("Nema MSISDN u bazi.")
    assert rows[0].broj > 0
