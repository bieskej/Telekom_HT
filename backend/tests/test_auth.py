import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import Radnik


@pytest.fixture
def admin_token(client: TestClient) -> str:
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_prijava_uspjesno(client: TestClient):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["radnik"]["uloga"] == "admin"
    assert data["radnik"]["email"] == "admin@eronet.ba"


def test_prijava_pogresna_lozinka(client: TestClient):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "pogresna"})
    assert res.status_code == 401


def test_statistike_bez_tokena(client: TestClient):
    res = client.get("/statistike")
    assert res.status_code == 401


def test_statistike_s_tokenom(client: TestClient, admin_token: str):
    res = client.get("/statistike", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert "ukupno" in res.json()


def test_dodijeli_bez_ovlasti(client: TestClient, admin_token: str, db):
    """Promet uloga nema pristup dodjeli."""
    from sqlalchemy import text

    db.execute(
        text(
            "DELETE FROM audit_log WHERE radnik_id IN (SELECT id FROM radnici WHERE email = 'promet@test.ba')"
        )
    )
    db.execute(text("DELETE FROM radnici WHERE email = 'promet@test.ba'"))
    db.add(
        Radnik(
            email="promet@test.ba",
            ime="Promet",
            prezime="Test",
            lozinka_hash=hash_password("test1234"),
            uloga="promet",
            aktivan=True,
        )
    )
    db.commit()

    login = client.post("/prijava", json={"email": "promet@test.ba", "lozinka": "test1234"})
    token = login.json()["access_token"]

    res = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "A",
            "prezime": "B",
            "jmbg": __import__("tests.conftest", fromlist=["VALID_JMBG"]).VALID_JMBG,
            "email": "a@b.com",
        },
    )
    assert res.status_code == 403

    db.execute(
        text(
            "DELETE FROM audit_log WHERE radnik_id IN (SELECT id FROM radnici WHERE email = 'promet@test.ba')"
        )
    )
    db.execute(text("DELETE FROM radnici WHERE email = 'promet@test.ba'"))
    db.commit()


def test_radnici_samo_admin(client: TestClient, admin_token: str):
    res = client.post(
        "/radnici",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "novi@test.ba",
            "ime": "Novi",
            "prezime": "Radnik",
            "lozinka": "lozinka123",
            "uloga": "prodaja",
        },
    )
    assert res.status_code == 201
    radnik_id = res.json()["id"]

    db = SessionLocal()
    try:
        db.execute(__import__("sqlalchemy").text("DELETE FROM radnici WHERE id = :id"), {"id": radnik_id})
        db.commit()
    finally:
        db.close()
