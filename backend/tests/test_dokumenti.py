import pytest
from sqlalchemy import text

from tests.conftest import VALID_JMBG


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _adresa_payload():
    return {
        "adresa": "Ulica Test 1",
        "grad": "Mostar",
        "postanski_broj": "88000",
    }


def _placanje_kartica():
    return {
        "placanje": {
            "nacin": "kartica",
            "broj_kartice": "4111111111111111",
            "datum_isteka": "12/28",
            "cvv": "123",
            "ime_vlasnika": "Test Korisnik",
        }
    }


def test_dodjela_gold_kartica_i_preuzimanje_pdf(client, db, slobodan_broj_mostar, auth_headers):
    if not slobodan_broj_mostar:
        pytest.skip("Nema slobodnih brojeva u Mostaru.")

    broj_id, _ = slobodan_broj_mostar
    gold = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one_or_none()
    if not gold:
        pytest.skip("Gold kvaliteta nije u bazi.")

    stari_kid = db.execute(
        text("SELECT kvaliteta_id FROM msisdn WHERE id = :id"), {"id": broj_id}
    ).scalar_one()
    db.execute(text("UPDATE msisdn SET kvaliteta_id = :g WHERE id = :id"), {"g": gold, "id": broj_id})
    db.commit()

    payload = {
        "opcina_naziv": "Mostar",
        "ime": "Test",
        "prezime": "Dokumenti",
        "jmbg": VALID_JMBG,
        "email": "test-dok@example.com",
        "kvaliteta_id": gold,
        **_adresa_payload(),
        **_placanje_kartica(),
    }
    res = client.post("/dodijeli-broj", headers=auth_headers, json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["kvaliteta"] == "gold"
    assert data["racun_url"] == f"/msisdn/{data['msisdn_id']}/racun"

    placanje = db.execute(
        text("SELECT nacin, status FROM placanja WHERE msisdn_id = :id ORDER BY id DESC LIMIT 1"),
        {"id": data["msisdn_id"]},
    ).fetchone()
    assert placanje is not None
    assert placanje.nacin == "kartica"
    assert placanje.status == "izvrseno"

    racun = client.get(f"/msisdn/{data['msisdn_id']}/racun", headers=auth_headers)
    assert racun.status_code == 200
    assert racun.headers["content-type"].startswith("application/pdf")
    assert racun.content[:4] == b"%PDF"
    assert b"DejaVuSans" in racun.content

    ugovor = client.get(f"/msisdn/{data['msisdn_id']}/ugovor", headers=auth_headers)
    assert ugovor.status_code == 200
    assert ugovor.content[:4] == b"%PDF"
    assert b"DejaVuSans" in ugovor.content

    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                email = NULL, adresa = NULL, grad = NULL, postanski_broj = NULL,
                datum_dodjele = NULL, kvaliteta_id = :kid
            WHERE id = :id
            """
        ),
        {"id": broj_id, "kid": stari_kid},
    )
    db.execute(text("DELETE FROM placanja WHERE msisdn_id = :id"), {"id": data["msisdn_id"]})
    db.commit()


def test_preuzimanje_racuna_prepisuje_stari_helvetica_cache(client, db, auth_headers):
    """GET /racun mora regenerirati PDF, ne vratiti stari Helvetica file s diska."""
    from app.services.document_storage import racun_path

    row = db.execute(
        text(
            """
            SELECT id FROM msisdn
            WHERE status = 'zauzet' AND ime IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        pytest.skip("Nema zauzetog broja za test cachea.")

    msisdn_id = row.id
    path = racun_path(msisdn_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n1 0 obj\n/BaseFont /Helvetica /Subtype /Type1\n")

    res = client.get(f"/msisdn/{msisdn_id}/racun", headers=auth_headers)
    assert res.status_code == 200, res.text
    assert b"DejaVuSans" in res.content
    assert path.read_bytes() == res.content


def test_pretraga_vraca_kvaliteta_naziv(client, auth_headers):
    res = client.get(
        "/msisdn/pretraga",
        params={"status": "zauzet", "per_page": 1},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    if body["rezultati"]:
        item = body["rezultati"][0]
        assert "kvaliteta_naziv" in item
        if item.get("kvaliteta"):
            assert item["kvaliteta_naziv"] == item["kvaliteta"]
