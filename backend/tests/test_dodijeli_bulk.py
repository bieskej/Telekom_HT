import pytest
from sqlalchemy import text

from app.auth.security import hash_password
from app.models import Radnik
from tests.conftest import VALID_JMBG


@pytest.fixture
def auth_headers(client):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    if res.status_code != 200:
        pytest.skip("Admin prijava nije uspjela – pokreni migrate_auth.sql")
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _obrisi_radnika(db, email: str) -> None:
    db.execute(
        text(
            "DELETE FROM audit_log WHERE radnik_id IN (SELECT id FROM radnici WHERE email = :email)"
        ),
        {"email": email},
    )
    db.execute(text("DELETE FROM radnici WHERE email = :email"), {"email": email})


@pytest.fixture
def prodaja_headers(client, db):
    email = "prodaja.bulk@test.ba"
    _obrisi_radnika(db, email)
    db.add(
        Radnik(
            email=email,
            ime="Prodaja",
            prezime="Bulk",
            lozinka_hash=hash_password("test1234"),
            uloga="prodaja",
            aktivan=True,
        )
    )
    db.commit()
    res = client.post("/prijava", json={"email": email, "lozinka": "test1234"})
    assert res.status_code == 200
    yield {"Authorization": f"Bearer {res.json()['access_token']}"}
    _obrisi_radnika(db, email)
    db.commit()


@pytest.fixture
def slobodni_brojevi_mostar(db, request):
    limit = getattr(request, "param", 3)
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
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    if len(rows) < limit:
        pytest.skip(f"Nedovoljno slobodnih brojeva u Mostaru (treba {limit}).")
    return rows


def _oslobodi_brojeve(db, ids: list[int], kvaliteta_id: int | None = None) -> None:
    if not ids:
        return
    if kvaliteta_id is None:
        kvaliteta_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()
    for msisdn_id in ids:
        db.execute(
            text(
                """
                UPDATE msisdn
                SET status = 'slobodan', jmbg = NULL, ime = NULL, prezime = NULL,
                    email = NULL, datum_dodjele = NULL, rezerviran_do = NULL,
                    kvaliteta_id = :kvaliteta_id
                WHERE id = :id
                """
            ),
            {"id": msisdn_id, "kvaliteta_id": kvaliteta_id},
        )
    db.commit()


def _postavi_kvalitetu(db, ids: list[int], naziv: str) -> int:
    kid = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = :n"), {"n": naziv}).scalar_one()
    for msisdn_id in ids:
        db.execute(
            text("UPDATE msisdn SET kvaliteta_id = :kid WHERE id = :id"),
            {"kid": kid, "id": msisdn_id},
        )
    db.commit()
    return kid


def _mostar_slobodni_svi_silver(db) -> None:
    silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver'")).scalar_one()
    db.execute(
        text(
            """
            UPDATE msisdn m
            SET kvaliteta_id = :silver_id
            FROM rasponi r
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE m.raspon_id = r.id
              AND o.naziv = 'Mostar'
              AND m.status = 'slobodan'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
            """
        ),
        {"silver_id": silver_id},
    )
    db.commit()


def test_generiraj_pdf_racun_bulk():
    from app.services.invoice_email import generiraj_pdf_racun_bulk

    pdf = generiraj_pdf_racun_bulk(
        "Test",
        "Korisnik",
        VALID_JMBG,
        "bulk@test.ba",
        ["+387 61 111 111", "+387 61 222 222"],
        "gold",
        25.0,
        2,
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_bulk_dodjela_default_silver(client, db, auth_headers, slobodni_brojevi_mostar):
    ids = [r.id for r in slobodni_brojevi_mostar[:2]]
    try:
        response = client.post(
            "/dodijeli-bulk",
            headers=auth_headers,
            json={
                "opcina_naziv": "Mostar",
                "broj_brojeva": 2,
                "korisnik_ime": "Bulk",
                "korisnik_prezime": "Silver",
                "korisnik_jmbg": VALID_JMBG,
                "adresa": "Ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
                "korisnik_email": "bulk-silver@test.ba",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dodijeljeno"] == 2
        assert data["kvaliteta"] == "silver"
        assert data["cijena_po_komadu"] == 10.0
        assert data["ukupna_cijena"] == 20.0

        for msisdn_id in ids:
            row = db.execute(
                text(
                    """
                    SELECT m.status, k.naziv AS kvaliteta
                    FROM msisdn m
                    JOIN kvaliteta k ON k.id = m.kvaliteta_id
                    WHERE m.id = :id
                    """
                ),
                {"id": msisdn_id},
            ).one()
            assert row.status == "zauzet"
            assert row.kvaliteta == "silver"
    finally:
        _oslobodi_brojeve(db, ids)


def test_bulk_dodjela_gold(client, db, auth_headers, slobodni_brojevi_mostar):
    ids = [r.id for r in slobodni_brojevi_mostar[:2]]
    gold_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one()
    try:
        _postavi_kvalitetu(db, ids, "gold")
        response = client.post(
            "/dodijeli-bulk",
            headers=auth_headers,
            json={
                "opcina_naziv": "Mostar",
                "broj_brojeva": 2,
                "korisnik_ime": "Bulk",
                "korisnik_prezime": "Gold",
                "korisnik_jmbg": VALID_JMBG,
                "adresa": "Ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
                "korisnik_email": "bulk-gold@test.ba",
                "kvaliteta_naziv": "gold",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kvaliteta"] == "gold"
        assert data["cijena_po_komadu"] == 25.0
        assert data["ukupna_cijena"] == 50.0

        row = db.execute(
            text("SELECT k.naziv FROM msisdn m JOIN kvaliteta k ON k.id = m.kvaliteta_id WHERE m.id = :id"),
            {"id": ids[0]},
        ).one()
        assert row.naziv == "gold"
    finally:
        _oslobodi_brojeve(db, ids, gold_id)


@pytest.mark.parametrize("slobodni_brojevi_mostar", [2], indirect=True)
def test_bulk_dodjela_gold_nedovoljno_404(client, db, auth_headers, slobodni_brojevi_mostar):
    """Traži 3 gold broja kad su u testu dostupna samo 2 označena gold."""
    ids = [r.id for r in slobodni_brojevi_mostar]
    gold_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'gold'")).scalar_one()
    stari = {
        i: db.execute(text("SELECT kvaliteta_id FROM msisdn WHERE id = :id"), {"id": i}).scalar_one()
        for i in ids
    }
    try:
        _mostar_slobodni_svi_silver(db)
        _postavi_kvalitetu(db, ids, "gold")
        res = client.post(
            "/dodijeli-bulk",
            headers=auth_headers,
            json={
                "opcina_naziv": "Mostar",
                "broj_brojeva": 3,
                "korisnik_ime": "Bulk",
                "korisnik_prezime": "GoldFail",
                "korisnik_jmbg": VALID_JMBG,
                "adresa": "Ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
                "korisnik_email": "bulk-gold-fail@test.ba",
                "kvaliteta_naziv": "gold",
            },
        )
        assert res.status_code == 404
        assert "gold" in res.json()["detail"].lower()
    finally:
        for msisdn_id in ids:
            _oslobodi_brojeve(db, [msisdn_id], stari[msisdn_id])


@pytest.mark.parametrize("slobodni_brojevi_mostar", [1], indirect=True)
def test_bulk_dodjela_platinum(client, db, auth_headers, slobodni_brojevi_mostar):
    msisdn_id = slobodni_brojevi_mostar[0].id
    platinum_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'platinum'")).scalar_one()
    try:
        _postavi_kvalitetu(db, [msisdn_id], "platinum")
        response = client.post(
            "/dodijeli-bulk",
            headers=auth_headers,
            json={
                "opcina_naziv": "Mostar",
                "broj_brojeva": 1,
                "korisnik_ime": "Bulk",
                "korisnik_prezime": "Platinum",
                "korisnik_jmbg": VALID_JMBG,
                "adresa": "Ulica 1",
                "grad": "Mostar",
                "postanski_broj": "88000",
                "korisnik_email": "bulk-platinum@test.ba",
                "kvaliteta_naziv": "platinum",
            },
        )
        assert response.status_code == 200
        assert response.json()["kvaliteta"] == "platinum"
        assert response.json()["ukupna_cijena"] == 50.0
    finally:
        _oslobodi_brojeve(db, [msisdn_id], platinum_id)


def test_bulk_dodjela_diamond_samo_admin(client, db, auth_headers, prodaja_headers, slobodni_brojevi_mostar):
    msisdn_id = slobodni_brojevi_mostar[0].id
    diamond_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'diamond'")).scalar_one()
    _postavi_kvalitetu(db, [msisdn_id], "diamond")
    payload = {
        "opcina_naziv": "Mostar",
        "broj_brojeva": 1,
        "korisnik_ime": "Bulk",
        "korisnik_prezime": "Diamond",
        "korisnik_jmbg": VALID_JMBG,
        "adresa": "Ulica 1",
        "grad": "Mostar",
        "postanski_broj": "88000",
        "korisnik_email": "bulk-diamond@test.ba",
        "kvaliteta_naziv": "diamond",
    }

    prodaja_res = client.post("/dodijeli-bulk", headers=prodaja_headers, json=payload)
    assert prodaja_res.status_code == 403

    try:
        admin_res = client.post("/dodijeli-bulk", headers=auth_headers, json=payload)
        assert admin_res.status_code == 200
        assert admin_res.json()["kvaliteta"] == "diamond"
        assert admin_res.json()["cijena_po_komadu"] == 100.0
    finally:
        _oslobodi_brojeve(db, [msisdn_id], diamond_id)
