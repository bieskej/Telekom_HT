"""Autentifikacija i autorizacija portala za kupce."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth.security import hash_password
from tests.conftest import VALID_JMBG, generiraj_validan_jmbg


def _registriraj_kupca(
    client: TestClient,
    email: str,
    jmbg: str | None = None,
    db=None,
) -> dict:
    jmbg = jmbg or generiraj_validan_jmbg(serijski="042")
    if db is not None:
        db.execute(
            text(
                "DELETE FROM kupac_kontakt WHERE kupac_id IN "
                "(SELECT id FROM radnici WHERE email = :e)"
            ),
            {"e": email},
        )
        db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
        db.commit()
    res = client.post(
        "/kupac/registracija",
        json={
            "ime": "Kupac",
            "prezime": "Test",
            "email": email,
            "jmbg": jmbg,
            "lozinka": "kupac1234",
        },
    )
    assert res.status_code == 201, res.text
    return {"email": email, "jmbg": jmbg, "lozinka": "kupac1234"}


def _kupac_token(client: TestClient, email: str, lozinka: str = "kupac1234") -> str:
    res = client.post("/kupac/prijava", json={"email": email, "lozinka": lozinka})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_registracija_kreira_kupca(client: TestClient, db):
    email = "kupac_reg@test.ba"
    pod = _registriraj_kupca(client, email, db=db)
    row = db.execute(
        text("SELECT uloga, jmbg FROM radnici WHERE email = :e"),
        {"e": email},
    ).fetchone()
    assert row.uloga == "kupac"
    assert row.jmbg == pod["jmbg"]
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_registracija_neispravan_jmbg_400(client: TestClient):
    res = client.post(
        "/kupac/registracija",
        json={
            "ime": "A",
            "prezime": "B",
            "email": "los_jmbg@test.ba",
            "jmbg": "1234567890123",
            "lozinka": "kupac1234",
        },
    )
    assert res.status_code == 400


def test_registracija_postojeci_email_409(client: TestClient, db):
    email = "kupac_dup@test.ba"
    _registriraj_kupca(client, email, db=db)
    res = client.post(
        "/kupac/registracija",
        json={
            "ime": "X",
            "prezime": "Y",
            "email": email,
            "jmbg": generiraj_validan_jmbg(serijski="043"),
            "lozinka": "kupac1234",
        },
    )
    assert res.status_code == 409
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_prijava_uspjesna_vraca_token(client: TestClient, db):
    email = "kupac_login@test.ba"
    _registriraj_kupca(client, email)
    res = client.post("/kupac/prijava", json={"email": email, "lozinka": "kupac1234"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["radnik"]["uloga"] == "kupac"
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_admin_token_ne_radi_na_kupac_rute_403(client: TestClient, admin_token: str):
    res = client.get(
        "/kupac/moji-brojevi",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403


def test_kupac_token_ne_radi_na_admin_rute_403(client: TestClient, db):
    email = "kupac_admin403@test.ba"
    _registriraj_kupca(client, email, db=db)
    token = _kupac_token(client, email)
    res = client.post(
        "/admin/import-rak",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert res.status_code == 403
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_kupac_ne_moze_staff_prijava(client: TestClient, db):
    email = "kupac_staff_prijava@test.ba"
    _registriraj_kupca(client, email, db=db)
    res = client.post("/prijava", json={"email": email, "lozinka": "kupac1234"})
    assert res.status_code == 403
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_kupac_token_ne_radi_na_radnici_403(client: TestClient, db):
    email = "kupac_radnici403@test.ba"
    _registriraj_kupca(client, email, db=db)
    token = _kupac_token(client, email)
    res = client.get("/radnici", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()
