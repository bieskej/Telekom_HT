from fastapi.testclient import TestClient
from sqlalchemy import text


def test_port_in_realizacija_kreira_msisdn(client: TestClient, db, admin_token: str):
    import uuid

    broj = f"39{uuid.uuid4().int % 10**8:08d}"
    res = client.post(
        "/portabilnost",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tip": "port_in",
            "broj": broj,
            "izvor_op": "Operator A",
            "ciljni_op": "HT d.d. Mostar",
        },
    )
    assert res.status_code == 200, res.text
    pid = res.json()["id"]
    for status in ("u_obradi", "realiziran"):
        r2 = client.patch(
            f"/portabilnost/{pid}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": status},
        )
        assert r2.status_code == 200, r2.text
    row = db.execute(text("SELECT id FROM msisdn WHERE broj = :b"), {"b": broj}).fetchone()
    assert row is not None


def test_port_out_realizacija_oznacava_status_portano(client: TestClient, db, admin_token: str):
    row = db.execute(
        text("SELECT id, broj FROM msisdn WHERE status = 'zauzet' LIMIT 1")
    ).fetchone()
    if not row:
        return
    res = client.post(
        "/portabilnost",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tip": "port_out",
            "msisdn_id": row.id,
            "izvor_op": "HT d.d. Mostar",
            "ciljni_op": "Operator B",
        },
    )
    assert res.status_code == 200
    pid = res.json()["id"]
    client.patch(
        f"/portabilnost/{pid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "u_obradi"},
    )
    client.patch(
        f"/portabilnost/{pid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "realiziran"},
    )
    status = db.execute(
        text("SELECT status FROM msisdn WHERE id = :id"), {"id": row.id}
    ).scalar()
    assert status == "portano"
    db.execute(text("UPDATE msisdn SET status = 'zauzet' WHERE id = :id"), {"id": row.id})
    db.commit()


def test_status_prelaz_validan(client: TestClient, admin_token: str):
    res = client.post(
        "/portabilnost",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "tip": "port_in",
            "broj": "3999998888",
            "izvor_op": "A",
            "ciljni_op": "HT",
        },
    )
    pid = res.json()["id"]
    bad = client.patch(
        f"/portabilnost/{pid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "realiziran"},
    )
    assert bad.status_code == 400
