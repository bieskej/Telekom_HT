import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


def test_korisnici_endpoint(client: TestClient, admin_token: str):
    res = client.get("/korisnici", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "jmbg" in item
        assert "broj_brojeva" in item
        assert "broj_zauzet" in item
        assert "broj_karantena" in item
        assert item["broj_brojeva"] >= 1


def test_korisnici_ukljucuje_karantenu(client: TestClient, admin_token: str, db, slobodan_broj_mostar):
    """Korisnik s brojem samo u karanteni mora biti vidljiv na /korisnici."""
    from tests.conftest import generiraj_validan_jmbg

    if not slobodan_broj_mostar:
        pytest.skip("Nema slobodnih brojeva u Mostaru za test.")

    broj_id, _ = slobodan_broj_mostar
    jmbg = generiraj_validan_jmbg(serijski="445")

    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                email = NULL, datum_dodjele = NULL, datum_karantene = NULL,
                karantena_razlog = NULL, rezerviran_do = NULL
            WHERE jmbg = :jmbg
            """
        ),
        {"jmbg": jmbg},
    )
    db.commit()

    rez = client.post(f"/rezerviraj/{broj_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert rez.status_code == 200, rez.text

    dodjela = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Karantena",
            "prezime": "Test",
            "jmbg": jmbg,
            "email": "karantena-korisnik@test.ba",
            "adresa": "Test ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
            "msisdn_id": broj_id,
        },
    )
    assert dodjela.status_code == 200, dodjela.text

    oslobodi = client.post(
        f"/oslobodi/{broj_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"karantena_dana": 60},
    )
    assert oslobodi.status_code == 200, oslobodi.text

    try:
        res = client.get("/korisnici", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        korisnik = next((k for k in res.json() if k["jmbg"] == jmbg), None)
        assert korisnik is not None, "Korisnik u karanteni nije na listi /korisnici"
        assert korisnik["broj_karantena"] >= 1
        assert korisnik["broj_zauzet"] == 0
    finally:
        db.execute(
            text(
                """
                UPDATE msisdn
                SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                    email = NULL, datum_dodjele = NULL, datum_karantene = NULL,
                    karantena_razlog = NULL, rezerviran_do = NULL
                WHERE jmbg = :jmbg
                """
            ),
            {"jmbg": jmbg},
        )
        db.commit()


def test_lokacije_hijerarhija(client: TestClient, admin_token: str):
    res = client.get("/lokacije-hijerarhija", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        group = data[0]
        assert "opcina_naziv" in group
        assert "lokacije" in group
        assert isinstance(group["lokacije"], list)


def test_msan_uredjaji(client: TestClient, admin_token: str):
    res = client.get("/msan-uredjaji", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "naziv" in item
        assert "opcina_naziv" in item
        assert "kapacitet" in item


def test_pretraga_korisnik_ime_prezime(client: TestClient, admin_token: str, db):
    row = db.execute(
        text(
            """
            SELECT ime, prezime
            FROM msisdn
            WHERE status = 'zauzet' AND ime IS NOT NULL AND TRIM(ime) <> ''
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        pytest.skip("Nema zauzetih brojeva s imenom u bazi")

    res = client.get(
        "/msisdn/pretraga",
        params={"korisnik_ime_prezime": row.ime[:3], "per_page": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ukupno"] >= 1
    assert any(
        (r.get("ime") or "").lower().find(row.ime[:3].lower()) >= 0
        or (r.get("prezime") or "").lower().find(row.ime[:3].lower()) >= 0
        for r in body["rezultati"]
    )


def test_pretraga_lokacija_id(client: TestClient, admin_token: str, db):
    row = db.execute(
        text(
            """
            SELECT l.id
            FROM lokacije l
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        pytest.skip("Nema brojeva povezanih s lokacijom")

    res = client.get(
        "/msisdn/pretraga",
        params={"lokacija_id": row.id, "per_page": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["ukupno"] >= 1
