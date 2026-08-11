"""Preuzimanje ugovora (PDF) za kupca — samo vlastiti brojevi."""

from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import generiraj_validan_jmbg
from tests.test_kupac_auth import _kupac_token, _registriraj_kupca


def test_pdf_download_uspjeh(client: TestClient, db, admin_token: str):
    jmbg = generiraj_validan_jmbg(serijski="061")
    email = "kupac_ugovor@test.ba"
    _registriraj_kupca(client, email, jmbg, db=db)
    token = _kupac_token(client, email)

    dodjela = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Kupac",
            "prezime": "Ugovor",
            "jmbg": jmbg,
            "email": email,
            "adresa": "Ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert dodjela.status_code == 200
    msisdn_id = dodjela.json()["msisdn_id"]

    res = client.get(
        f"/kupac/ugovor/{msisdn_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content[:4] == b"%PDF"

    client.post(
        f"/oslobodi/{msisdn_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_pdf_download_tudji_broj_403(client: TestClient, db, admin_token: str):
    jmbg_vlasnik = generiraj_validan_jmbg(serijski="062")
    jmbg_tudji = generiraj_validan_jmbg(serijski="063")
    email_v = "kupac_vlasnik@test.ba"
    email_t = "kupac_tudji@test.ba"
    _registriraj_kupca(client, email_v, jmbg_vlasnik, db=db)
    _registriraj_kupca(client, email_t, jmbg_tudji, db=db)
    token_t = _kupac_token(client, email_t)

    dodjela = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Vlasnik",
            "prezime": "Broja",
            "jmbg": jmbg_vlasnik,
            "email": email_v,
            "adresa": "Ulica 3",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert dodjela.status_code == 200
    msisdn_id = dodjela.json()["msisdn_id"]

    res = client.get(
        f"/kupac/ugovor/{msisdn_id}",
        headers={"Authorization": f"Bearer {token_t}"},
    )
    assert res.status_code == 403

    client.post(
        f"/oslobodi/{msisdn_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    db.execute(text("DELETE FROM radnici WHERE email IN (:a, :b)"), {"a": email_v, "b": email_t})
    db.commit()
