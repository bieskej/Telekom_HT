"""Provjera JMBG-a prije dodjele — informativni endpoint."""

import pytest
from sqlalchemy import text

from tests.conftest import VALID_JMBG, generiraj_validan_jmbg
from tests.test_kupac_auth import _registriraj_kupca


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela – pokreni migrate_auth.sql")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_provjeri_jmbg_neispravan(client, auth_headers):
    res = client.get(
        "/msisdn/provjeri-jmbg",
        headers=auth_headers,
        params={"jmbg": "1234567890123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert data["postojeci_brojevi"] == 0
    assert "modul 11" in data["upozorenja"][0].lower()


def test_provjeri_jmbg_bez_povijesti(client, auth_headers):
    jmbg = generiraj_validan_jmbg(serijski="111")
    res = client.get(
        "/msisdn/provjeri-jmbg",
        headers=auth_headers,
        params={"jmbg": jmbg, "ime": "Novi", "prezime": "Korisnik"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["jmbg"] == jmbg
    assert data["postojeci_brojevi"] == 0
    assert data["upozorenja"] == []
    assert data["portal_korisnik"] is None


def test_provjeri_jmbg_razlicito_ime(client, db, auth_headers, slobodan_broj_mostar):
    if not slobodan_broj_mostar:
        pytest.skip("Nema slobodnih brojeva u Mostaru za test.")

    broj_id, _ = slobodan_broj_mostar
    jmbg = generiraj_validan_jmbg(serijski="222")

    rez = client.post(f"/rezerviraj/{broj_id}", headers=auth_headers)
    assert rez.status_code == 200, rez.text

    dodjela = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Stari",
            "prezime": "Korisnik",
            "jmbg": jmbg,
            "email": "stari@test.ba",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
            "msisdn_id": broj_id,
        },
    )
    assert dodjela.status_code == 200, dodjela.text

    try:
        res = client.get(
            "/msisdn/provjeri-jmbg",
            headers=auth_headers,
            params={"jmbg": jmbg, "ime": "Novo", "prezime": "Ime"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["postojeci_brojevi"] == 1
        assert data["prethodno_ime"] == "Stari"
        assert data["prethodno_prezime"] == "Korisnik"
        assert any("Prethodno zabilježeno ime" in u for u in data["upozorenja"])
        assert any("1 dodijeljenih brojeva" in u for u in data["upozorenja"])
    finally:
        db.execute(
            text(
                """
                UPDATE msisdn
                SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                    email = NULL, datum_dodjele = NULL, rezerviran_do = NULL
                WHERE jmbg = :jmbg
                """
            ),
            {"jmbg": jmbg},
        )
        db.commit()


def test_provjeri_jmbg_portal_korisnik(client, db, auth_headers):
    jmbg = generiraj_validan_jmbg(serijski="333")
    email = "portal_provjera@test.ba"
    _registriraj_kupca(client, email, jmbg=jmbg, db=db)

    try:
        res = client.get(
            "/msisdn/provjeri-jmbg",
            headers=auth_headers,
            params={"jmbg": jmbg, "ime": "Drugo", "prezime": "Ime"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["portal_korisnik"] is not None
        assert data["portal_korisnik"]["ime"] == "Kupac"
        assert data["portal_korisnik"]["prezime"] == "Test"
        assert data["portal_korisnik"]["email"] == email
        assert any("Registriran kupac portala" in u for u in data["upozorenja"])
    finally:
        db.execute(
            text(
                "DELETE FROM kupac_kontakt WHERE kupac_id IN "
                "(SELECT id FROM radnici WHERE email = :e)"
            ),
            {"e": email},
        )
        db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
        db.commit()


def test_dodijeli_normalizira_jmbg(client, db, auth_headers, slobodan_broj_mostar):
    if not slobodan_broj_mostar:
        pytest.skip("Nema slobodnih brojeva u Mostaru za test.")

    broj_id, _ = slobodan_broj_mostar
    jmbg = VALID_JMBG

    rez = client.post(f"/rezerviraj/{broj_id}", headers=auth_headers)
    assert rez.status_code == 200, rez.text

    response = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Test",
            "prezime": "Norm",
            "jmbg": f" {jmbg} ",
            "email": "norm@test.ba",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
            "msisdn_id": broj_id,
        },
    )
    assert response.status_code == 200, response.text

    row = db.execute(
        text("SELECT jmbg FROM msisdn WHERE id = :id"),
        {"id": broj_id},
    ).one()
    assert row.jmbg == jmbg

    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                email = NULL, datum_dodjele = NULL, rezerviran_do = NULL
            WHERE id = :id
            """
        ),
        {"id": broj_id},
    )
    db.commit()


def test_dodijeli_neispravan_postanski(client, auth_headers):
    response = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Test",
            "prezime": "Korisnik",
            "jmbg": VALID_JMBG,
            "email": "test@example.com",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "8800",
        },
    )
    assert response.status_code == 400
    assert "poštanski" in response.json()["detail"].lower()
