from fastapi.testclient import TestClient
from sqlalchemy import text


def test_wildcard_zvijezda_7777_vraca_diamond(client: TestClient, db, admin_token: str):
    row = db.execute(
        text(
            """
            SELECT m.id FROM msisdn m
            JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE m.status = 'slobodan'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
              AND k.naziv = 'diamond'
              AND m.broj LIKE '%7777'
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return
    res = client.get(
        "/msisdn/wildcard",
        params={"uzorak": "*7777", "kvaliteta_id": db.execute(text("SELECT id FROM kvaliteta WHERE naziv='diamond'")).scalar(), "limit": 50},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ukupno"] >= 1
    assert all(r["kvaliteta"] == "diamond" for r in body["rezultati"])
    assert all(r["broj"].endswith("7777") for r in body["rezultati"])


def test_wildcard_filter_po_opcini(client: TestClient, db, admin_token: str):
    res = client.get(
        "/msisdn/wildcard",
        params={"uzorak": "*0", "opcina_naziv": "Mostar", "limit": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    for r in res.json()["rezultati"]:
        assert r["opcina_naziv"] and "mostar" in r["opcina_naziv"].lower()


def test_wildcard_ne_vraca_rezervirane(client: TestClient, db, admin_token: str):
    row = db.execute(
        text(
            """
            SELECT m.id, m.broj FROM msisdn m
            WHERE m.status = 'slobodan'
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return
    suf = row.broj[-4:]
    db.execute(
        text(
            "UPDATE msisdn SET rezerviran_do = NOW() + interval '10 minutes' WHERE id = :id"
        ),
        {"id": row.id},
    )
    db.commit()
    res = client.get(
        "/msisdn/wildcard",
        params={"uzorak": f"*{suf}", "limit": 50},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    ids = [r["id"] for r in res.json()["rezultati"]]
    assert row.id not in ids
    db.execute(text("UPDATE msisdn SET rezerviran_do = NULL WHERE id = :id"), {"id": row.id})
    db.commit()
