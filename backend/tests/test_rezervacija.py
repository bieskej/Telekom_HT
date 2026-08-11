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


def _prvi_slobodan_mostar(db):
    """Prvi slobodan silver broj (default pri rezervaciji bez kvaliteta_id)."""
    return db.execute(
        text(
            """
            SELECT m.id, m.broj
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE o.naziv = 'Mostar'
              AND m.status = 'slobodan'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
              AND k.naziv = 'silver'
            ORDER BY m.broj
            LIMIT 1
            """
        )
    ).one_or_none()


def test_rezerviraj_sljedeci_prvi_u_opcini(client, db, auth_headers):
    prvi = _prvi_slobodan_mostar(db)
    if not prvi:
        pytest.skip("Nema slobodnih brojeva u Mostaru.")

    prvi_id, prvi_broj = prvi.id, prvi.broj

    res = client.post(
        "/rezerviraj-sljedeci",
        headers=auth_headers,
        json={"opcina_naziv": "Mostar"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["msisdn_id"] == prvi_id
    assert data["broj"] == prvi_broj
    assert data["broj_formatiran"].startswith("+387 ")
    assert data["preostalo_sekundi"] > 0

    rezerviran_do = db.execute(
        text("SELECT rezerviran_do FROM msisdn WHERE id = :id"),
        {"id": prvi_id},
    ).scalar_one()
    assert rezerviran_do is not None

    client.delete(f"/rezerviraj/{prvi_id}", headers=auth_headers)


def test_rezerviraj_sljedeci_novi_broj_preskace_prethodni(client, db, auth_headers):
    """Simulira UI gumb 'Novi broj': poništi rezervaciju pa rezerviraj sljedeći, ali bez ponavljanja."""
    prvi = _prvi_slobodan_mostar(db)
    if not prvi:
        pytest.skip("Nema slobodnih brojeva u Mostaru.")

    # 1) rezerviraj prvi
    rez1 = client.post(
        "/rezerviraj-sljedeci",
        headers=auth_headers,
        json={"opcina_naziv": "Mostar"},
    )
    assert rez1.status_code == 200, rez1.text
    a = rez1.json()["msisdn_id"]

    # 2) poništi
    del1 = client.delete(f"/rezerviraj/{a}", headers=auth_headers)
    assert del1.status_code in (200, 204), del1.text

    # 3) rezerviraj sljedeći, ali preskoči prethodni
    rez2 = client.post(
        "/rezerviraj-sljedeci",
        headers=auth_headers,
        json={"opcina_naziv": "Mostar", "exclude_msisdn_id": a},
    )
    if rez2.status_code != 200:
        pytest.skip("Nema drugog slobodnog broja u Mostaru za test preskakanja.")
    b = rez2.json()["msisdn_id"]
    assert b != a

    client.delete(f"/rezerviraj/{b}", headers=auth_headers)


def test_rezerviraj_sljedeci_pa_dodjela_isti_broj(client, db, auth_headers):
    prvi = _prvi_slobodan_mostar(db)
    if not prvi:
        pytest.skip("Nema slobodnih brojeva u Mostaru.")

    prvi_id, prvi_broj = prvi.id, prvi.broj

    rez = client.post(
        "/rezerviraj-sljedeci",
        headers=auth_headers,
        json={"opcina_naziv": "Mostar"},
    )
    assert rez.status_code == 200
    msisdn_id = rez.json()["msisdn_id"]
    assert msisdn_id == prvi_id

    silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()

    dodjela = client.post(
        "/dodijeli-broj",
        headers=auth_headers,
        json={
            "opcina_naziv": "Mostar",
            "ime": "Rez",
            "prezime": "Sljedeci",
            "jmbg": VALID_JMBG,
            "email": "rez-sljedeci@example.com",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
            "msisdn_id": msisdn_id,
            "kvaliteta_id": silver_id,
        },
    )
    assert dodjela.status_code == 200, dodjela.text
    assert dodjela.json()["broj"] == prvi_broj
    assert dodjela.json()["msisdn_id"] == prvi_id

    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                email = NULL, datum_dodjele = NULL, rezerviran_do = NULL
            WHERE id = :id
            """
        ),
        {"id": prvi_id},
    )
    db.commit()
