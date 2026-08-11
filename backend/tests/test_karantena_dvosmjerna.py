from fastapi.testclient import TestClient
from sqlalchemy import text


def _zauzet_broj(db) -> int | None:
    row = db.execute(
        text("SELECT id FROM msisdn WHERE status = 'zauzet' LIMIT 1")
    ).fetchone()
    return row.id if row else None


def _u_karantenu(client: TestClient, token: str, msisdn_id: int, dana: int = 60) -> None:
    res = client.post(
        f"/oslobodi/{msisdn_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"karantena_dana": dana},
    )
    assert res.status_code == 200, res.text


def test_produzi_dana_pomice_datum_naprijed(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 30)
    prije = db.execute(
        text("SELECT karantena_dana, datum_karantene FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).one()
    res = client.patch(
        f"/msisdn/{msisdn_id}/karantena",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"produzi_dana": 15},
    )
    assert res.status_code == 200, res.text
    poslije = db.execute(
        text("SELECT karantena_dana FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).scalar()
    assert poslije == prije.karantena_dana + 15
    body = res.json()
    assert body["karantena_dana"] == poslije


def test_skrati_dana_admin_only(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 60)
    res = client.patch(
        f"/msisdn/{msisdn_id}/karantena",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"skrati_dana": 10},
    )
    assert res.status_code == 200, res.text
    dana = db.execute(
        text("SELECT karantena_dana FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).scalar()
    assert dana == 50


def test_skrati_prodaja_403(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 40)
    prodaja = client.post("/prijava", json={"email": "prodaja@eronet.ba", "lozinka": "prodaja"})
    if prodaja.status_code != 200:
        return
    prodaja_token = prodaja.json()["access_token"]
    res = client.patch(
        f"/msisdn/{msisdn_id}/karantena",
        headers={"Authorization": f"Bearer {prodaja_token}"},
        json={"skrati_dana": 5},
    )
    assert res.status_code == 403


def test_oslobodi_admin_vraca_status_slobodan(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 20)
    res = client.post(
        f"/msisdn/{msisdn_id}/oslobodi",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"razlog": "Test admin oslobađanje"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "slobodan"
    status = db.execute(
        text("SELECT status, datum_karantene FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).one()
    assert status.status == "slobodan"
    assert status.datum_karantene is None
    hist = db.execute(
        text(
            """
            SELECT akcija FROM msisdn_history
            WHERE msisdn_id = :id AND akcija = 'oslobodeno_iz_karantene'
            ORDER BY id DESC LIMIT 1
            """
        ),
        {"id": msisdn_id},
    ).fetchone()
    assert hist is not None


def test_oslobodi_prodaja_403(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 20)
    prodaja = client.post("/prijava", json={"email": "prodaja@eronet.ba", "lozinka": "prodaja"})
    if prodaja.status_code != 200:
        return
    prodaja_token = prodaja.json()["access_token"]
    res = client.post(
        f"/msisdn/{msisdn_id}/oslobodi",
        headers={"Authorization": f"Bearer {prodaja_token}"},
        json={},
    )
    assert res.status_code == 403


def test_vrati_aktivno_zadrzava_jmbg(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    jmbg_prije = db.execute(
        text("SELECT jmbg FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).scalar()
    if not jmbg_prije:
        return
    _u_karantenu(client, admin_token, msisdn_id, 30)
    res = client.post(
        f"/msisdn/{msisdn_id}/vrati-aktivno",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"razlog": "Test povrat u aktivno"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "zauzet"
    row = db.execute(
        text("SELECT status, jmbg, datum_karantene FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).one()
    assert row.status == "zauzet"
    assert row.jmbg == jmbg_prije
    assert row.datum_karantene is None
    hist = db.execute(
        text(
            """
            SELECT akcija FROM msisdn_history
            WHERE msisdn_id = :id AND akcija = 'vraceno_u_aktivno'
            ORDER BY id DESC LIMIT 1
            """
        ),
        {"id": msisdn_id},
    ).fetchone()
    assert hist is not None


def test_vrati_aktivno_prodaja_ok(client: TestClient, db, admin_token: str):
    msisdn_id = _zauzet_broj(db)
    if not msisdn_id:
        return
    _u_karantenu(client, admin_token, msisdn_id, 20)
    prodaja = client.post("/prijava", json={"email": "prodaja@eronet.ba", "lozinka": "prodaja"})
    if prodaja.status_code != 200:
        return
    prodaja_token = prodaja.json()["access_token"]
    res = client.post(
        f"/msisdn/{msisdn_id}/vrati-aktivno",
        headers={"Authorization": f"Bearer {prodaja_token}"},
        json={},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "zauzet"
