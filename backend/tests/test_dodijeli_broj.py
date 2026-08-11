import pytest
from sqlalchemy import text

from tests.conftest import VALID_JMBG


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela – pokreni migrate_auth.sql")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dodijeli_broj_uspjesno(client, db, slobodan_broj_mostar, auth_headers):
    if not slobodan_broj_mostar:
        pytest.skip("Nema slobodnih brojeva u Mostaru za test.")

    broj_id, broj_raw = slobodan_broj_mostar

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
            "postanski_broj": "88000",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "zauzet"
    assert data["kvaliteta"] == "silver"
    assert data["broj"] == broj_raw
    assert data["broj_formatiran"].startswith("+387 ")
    assert "racun_url" in data
    assert "ugovor_url" in data

    row = db.execute(
        text("SELECT status, jmbg, ime FROM msisdn WHERE id = :id"),
        {"id": broj_id},
    ).one()
    assert row.status == "zauzet"
    assert row.jmbg == VALID_JMBG
    assert row.ime == "Test"

    # Vrati broj u slobodan za idempotentnost ostalih testova
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


def test_dodijeli_broj_neispravan_jmbg(client, auth_headers):
    response = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Test",
            "prezime": "Korisnik",
            "jmbg": "1234567890123",
            "email": "test@example.com",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert response.status_code == 400
    assert "JMBG" in response.json()["detail"]


def test_dodijeli_broj_nema_slobodnih(client, db, auth_headers):
    """Općina u županiji BEZ ijednog MSISDN-a → 404 (i županijski pool prazan)."""
    opcina_naziv = "TestOpcinaBezBrojeva"
    db.execute(text("DELETE FROM opcine WHERE naziv = :n"), {"n": opcina_naziv})
    db.execute(text("DELETE FROM zupanije WHERE oznaka = 'TST'"))
    db.commit()
    db.execute(
        text(
            """
            INSERT INTO zupanije (oznaka, naziv, entitet, sjediste)
            VALUES ('TST', 'TestRegija', 'RS', 'TestSjediste')
            """
        )
    )
    db.execute(
        text(
            """
            INSERT INTO opcine (naziv, zupanija_id, entitet)
            SELECT :naziv, id, 'RS' FROM zupanije WHERE oznaka = 'TST'
            """
        ),
        {"naziv": opcina_naziv},
    )
    db.commit()

    try:
        response = client.post(
            "/dodijeli-broj",
            headers=auth_headers,
            json={
                "opcina_naziv": opcina_naziv,
                "ime": "Test",
                "prezime": "Korisnik",
                "jmbg": VALID_JMBG,
                "email": "test@example.com",
                "adresa": "Test ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
            },
        )
        assert response.status_code == 404
        assert "slobodnih" in response.json()["detail"].lower()
    finally:
        db.execute(text("DELETE FROM opcine WHERE naziv = :n"), {"n": opcina_naziv})
        db.execute(text("DELETE FROM zupanije WHERE oznaka = 'TST'"))
        db.commit()


def test_dodijeli_rezervirani_msisdn_id(client, db, auth_headers):
    """Rezervira drugi po redu slobodan broj, dodijeli ga po ID-u – ne smije uzeti prvog slobodnog."""
    rows = db.execute(
        text(
            """
            SELECT m.id, m.broj
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE o.naziv = 'Mostar'
              AND m.status = 'slobodan'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
            ORDER BY m.broj
            LIMIT 2
            """
        )
    ).fetchall()
    if len(rows) < 2:
        pytest.skip("Potrebna su barem 2 slobodna broja u Mostaru.")

    prvi_id, prvi_broj = rows[0].id, rows[0].broj
    rezervirani_id, rezervirani_broj = rows[1].id, rows[1].broj
    assert prvi_broj != rezervirani_broj

    silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()
    db.execute(
        text("UPDATE msisdn SET kvaliteta_id = :s WHERE id IN (:a, :b)"),
        {"s": silver_id, "a": prvi_id, "b": rezervirani_id},
    )
    db.commit()

    rez = client.post(f"/rezerviraj/{rezervirani_id}", headers=auth_headers)
    assert rez.status_code == 200, rez.text

    response = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Rezervacija",
            "prezime": "Test",
            "jmbg": VALID_JMBG,
            "email": "rezervacija-test@example.com",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
            "msisdn_id": rezervirani_id,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["broj"] == rezervirani_broj
    assert data["broj"] != prvi_broj
    assert data["msisdn_id"] == rezervirani_id
    assert data["status"] == "zauzet"

    prvi_status = db.execute(
        text("SELECT status FROM msisdn WHERE id = :id"), {"id": prvi_id}
    ).scalar_one()
    assert prvi_status == "slobodan"

    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                email = NULL, adresa = NULL, grad = NULL, postanski_broj = NULL,
                datum_dodjele = NULL, rezerviran_do = NULL
            WHERE id = :id
            """
        ),
        {"id": rezervirani_id},
    )
    db.commit()
