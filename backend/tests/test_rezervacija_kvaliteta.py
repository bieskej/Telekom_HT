"""Rezervacija i dodjela filtriraju po inherentnoj kvaliteti broja u bazi."""

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


def _dva_slobodna_mostar(db):
    return db.execute(
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


def _vrati_stanje(db, stanja: list[tuple[int, int | None, str | None]]) -> None:
    for msisdn_id, kvaliteta_id, status in stanja:
        db.execute(
            text(
                """
                UPDATE msisdn
                SET kvaliteta_id = :kid, status = :status,
                    jmbg = NULL, ime = NULL, prezime = NULL, email = NULL,
                    datum_dodjele = NULL, rezerviran_do = NULL
                WHERE id = :id
                """
            ),
            {"id": msisdn_id, "kid": kvaliteta_id, "status": status},
        )
    db.commit()


def test_rezerviraj_sljedeci_gold_ne_uzima_silver(client, db, auth_headers):
    rows = _dva_slobodna_mostar(db)
    if len(rows) < 2:
        pytest.skip("Potrebna su 2 slobodna broja u Mostaru.")

    prvi_id, prvi_broj = rows[0].id, rows[0].broj
    drugi_id = rows[1].id

    silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()
    gold_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one()

    stari = [
        (prvi_id, db.execute(text("SELECT kvaliteta_id FROM msisdn WHERE id = :id"), {"id": prvi_id}).scalar_one(), "slobodan"),
        (drugi_id, db.execute(text("SELECT kvaliteta_id FROM msisdn WHERE id = :id"), {"id": drugi_id}).scalar_one(), "slobodan"),
    ]

    try:
        db.execute(
            text("UPDATE msisdn SET kvaliteta_id = :g WHERE id = :id"),
            {"g": gold_id, "id": prvi_id},
        )
        db.execute(
            text("UPDATE msisdn SET kvaliteta_id = :s WHERE id = :id"),
            {"s": silver_id, "id": drugi_id},
        )
        db.commit()

        res = client.post(
            "/rezerviraj-sljedeci",
            headers=auth_headers,
            json={"opcina_naziv": "Mostar", "kvaliteta_id": gold_id},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["msisdn_id"] == prvi_id
        assert data["broj"] == prvi_broj

        client.delete(f"/rezerviraj/{prvi_id}", headers=auth_headers)
    finally:
        _vrati_stanje(
            db,
            [(prvi_id, stari[0][1], "slobodan"), (drugi_id, stari[1][1], "slobodan")],
        )


def test_dodjela_zadrzava_gold_kvalitetu(client, db, auth_headers):
    rows = _dva_slobodna_mostar(db)
    if len(rows) < 1:
        pytest.skip("Nema slobodnih brojeva u Mostaru.")

    msisdn_id = rows[0].id
    gold_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one()
    stari_kid = db.execute(
        text("SELECT kvaliteta_id FROM msisdn WHERE id = :id"), {"id": msisdn_id}
    ).scalar_one()

    try:
        db.execute(
            text("UPDATE msisdn SET kvaliteta_id = :g WHERE id = :id"),
            {"g": gold_id, "id": msisdn_id},
        )
        db.commit()

        rez = client.post(
            "/rezerviraj-sljedeci",
            headers=auth_headers,
            json={"opcina_naziv": "Mostar", "kvaliteta_id": gold_id},
        )
        assert rez.status_code == 200
        assert rez.json()["msisdn_id"] == msisdn_id

        dodjela = client.post(
            "/dodijeli-broj",
            headers=auth_headers,
            json={
                "opcina_naziv": "Mostar",
                "ime": "Gold",
                "prezime": "Korisnik",
                "jmbg": VALID_JMBG,
                "email": "gold-kval@test.ba",
                "adresa": "Ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
                "msisdn_id": msisdn_id,
                "kvaliteta_id": gold_id,
            },
        )
        assert dodjela.status_code == 200, dodjela.text
        assert dodjela.json()["kvaliteta"] == "gold"

        kid_poslije = db.execute(
            text(
                """
                SELECT k.naziv FROM msisdn m
                JOIN kvaliteta k ON k.id = m.kvaliteta_id
                WHERE m.id = :id
                """
            ),
            {"id": msisdn_id},
        ).scalar_one()
        assert kid_poslije == "gold"
    finally:
        _vrati_stanje(db, [(msisdn_id, stari_kid, "slobodan")])
