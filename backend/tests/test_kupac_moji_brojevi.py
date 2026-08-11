"""Kupac vidi samo brojeve povezane s vlastitim JMBG-om."""

from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import VALID_JMBG, generiraj_validan_jmbg
from tests.test_kupac_auth import _kupac_token, _registriraj_kupca


def test_vraca_samo_brojeve_s_istim_jmbg(client: TestClient, db, admin_token: str):
    jmbg_kupca = generiraj_validan_jmbg(serijski="051")
    email = "kupac_brojevi@test.ba"
    _registriraj_kupca(client, email, jmbg_kupca, db=db)
    token = _kupac_token(client, email)

    # Dodijeli broj s istim JMBG-om
    dodjela = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Kupac",
            "prezime": "Test",
            "jmbg": jmbg_kupca,
            "email": email,
            "adresa": "Ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert dodjela.status_code == 200, dodjela.text
    msisdn_id = dodjela.json()["msisdn_id"]

    res = client.get(
        "/kupac/moji-brojevi",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ukupno"] >= 1
    brojevi_ids = [b["id"] for b in body["brojevi"]]
    assert msisdn_id in brojevi_ids

    # Očisti
    client.post(
        f"/oslobodi/{msisdn_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    db.execute(text("DELETE FROM radnici WHERE email = :e"), {"e": email})
    db.commit()


def test_ne_vraca_brojeve_drugog_kupca(client: TestClient, db, admin_token: str):
    jmbg_a = generiraj_validan_jmbg(serijski="052")
    jmbg_b = generiraj_validan_jmbg(serijski="053")
    email_a = "kupac_a@test.ba"
    email_b = "kupac_b@test.ba"
    _registriraj_kupca(client, email_a, jmbg_a, db=db)
    _registriraj_kupca(client, email_b, jmbg_b, db=db)
    token_a = _kupac_token(client, email_a)

    dodjela_b = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Drugi",
            "prezime": "Kupac",
            "jmbg": jmbg_b,
            "email": email_b,
            "adresa": "Ulica 2",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    assert dodjela_b.status_code == 200
    msisdn_b = dodjela_b.json()["msisdn_id"]

    res = client.get(
        "/kupac/moji-brojevi",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 200
    brojevi_ids = [b["id"] for b in res.json()["brojevi"]]
    assert msisdn_b not in brojevi_ids

    client.post(
        f"/oslobodi/{msisdn_b}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    db.execute(text("DELETE FROM radnici WHERE email IN (:a, :b)"), {"a": email_a, "b": email_b})
    db.commit()
