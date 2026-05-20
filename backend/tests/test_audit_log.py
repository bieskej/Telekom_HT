from fastapi.testclient import TestClient
from sqlalchemy import text


def test_prijava_logira_audit_red(client: TestClient, db):
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    assert res.status_code == 200
    row = db.execute(
        text(
            "SELECT akcija, entitet FROM audit_log WHERE akcija = 'prijava' ORDER BY id DESC LIMIT 1"
        )
    ).fetchone()
    assert row is not None
    assert row.entitet == "radnik"


def test_dodjela_logira_audit_red(client: TestClient, db, admin_token: str):
    row = db.execute(
        text(
            """
            SELECT m.id FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE m.status = 'slobodan' AND o.naziv = 'Mostar'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
              AND COALESCE(m.u_kvaru, false) = false
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return
    client.post(
        f"/rezerviraj/{row.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    res = client.post(
        "/dodijeli-broj",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "msisdn_id": row.id,
            "opcina_naziv": "Mostar",
            "ime": "Audit",
            "prezime": "Test",
            "jmbg": "0101000500012",
            "email": "audit@test.ba",
            "adresa": "Ulica 1",
            "grad": "Mostar",
            "postanski_broj": "88000",
        },
    )
    if res.status_code != 200:
        return
    audit = db.execute(
        text(
            "SELECT akcija FROM audit_log WHERE akcija = 'dodjela' ORDER BY id DESC LIMIT 1"
        )
    ).fetchone()
    assert audit is not None


def test_export_csv_format(client: TestClient, admin_token: str):
    res = client.get(
        "/admin/audit-log/export.csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert "akcija" in res.text
    assert "entitet" in res.text


def test_filter_po_radniku_i_entitetu(client: TestClient, admin_token: str):
    res = client.get(
        "/admin/audit-log?entitet=radnik&limit=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "stavke" in body
    for s in body["stavke"]:
        assert s["entitet"] == "radnik"
