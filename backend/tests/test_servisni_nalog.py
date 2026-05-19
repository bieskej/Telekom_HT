from fastapi.testclient import TestClient
from sqlalchemy import text

from app.services.msisdn_service import _find_slobodan_ids


def _uredjaj_s_msisdn(db):
    return db.execute(
        text(
            """
            SELECT u.id AS uredjaj_id, o.naziv AS opcina
            FROM uredjaji u
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            WHERE m.status = 'slobodan'
            LIMIT 1
            """
        )
    ).fetchone()


def test_kriticni_nalog_blokira_msisdne_uredjaja(client: TestClient, db, admin_token: str):
    row = _uredjaj_s_msisdn(db)
    if not row:
        return
    res = client.post(
        "/servisni-nalozi",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"uredjaj_id": row.uredjaj_id, "opis": "Kvar MSAN", "prioritet": "kritican"},
    )
    assert res.status_code == 200
    u_kvaru = db.execute(
        text(
            """
            SELECT COUNT(*)::int FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            WHERE r.uredjaj_id = :uid AND m.u_kvaru = true
            """
        ),
        {"uid": row.uredjaj_id},
    ).scalar()
    assert u_kvaru > 0
    client.patch(
        f"/servisni-nalozi/{res.json()['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "rijesen"},
    )


def test_zatvaranje_naloga_skida_u_kvaru_flag(client: TestClient, db, admin_token: str):
    row = _uredjaj_s_msisdn(db)
    if not row:
        return
    db.execute(
        text(
            """
            UPDATE servisni_nalog SET status = 'rijesen', rijeseno_at = NOW()
            WHERE uredjaj_id = :uid AND prioritet = 'kritican' AND status != 'rijesen'
            """
        ),
        {"uid": row.uredjaj_id},
    )
    db.execute(
        text(
            """
            UPDATE msisdn m SET u_kvaru = false
            FROM rasponi r WHERE r.id = m.raspon_id AND r.uredjaj_id = :uid
            """
        ),
        {"uid": row.uredjaj_id},
    )
    db.commit()
    prije = db.execute(
        text(
            """
            SELECT COUNT(*)::int FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            WHERE r.uredjaj_id = :uid AND m.u_kvaru = true
            """
        ),
        {"uid": row.uredjaj_id},
    ).scalar()
    res = client.post(
        "/servisni-nalozi",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"uredjaj_id": row.uredjaj_id, "opis": "Test zatvaranje", "prioritet": "kritican"},
    )
    nid = res.json()["id"]
    tijekom = db.execute(
        text(
            """
            SELECT COUNT(*)::int FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            WHERE r.uredjaj_id = :uid AND m.u_kvaru = true
            """
        ),
        {"uid": row.uredjaj_id},
    ).scalar()
    assert tijekom > prije
    client.patch(
        f"/servisni-nalozi/{nid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "rijesen"},
    )
    db.expire_all()
    poslije = db.execute(
        text(
            """
            SELECT COUNT(*)::int FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            WHERE r.uredjaj_id = :uid AND m.u_kvaru = true
            """
        ),
        {"uid": row.uredjaj_id},
    ).scalar()
    assert poslije == 0


def test_find_slobodan_preskace_u_kvaru(db):
    row = db.execute(
        text(
            """
            SELECT m.id, o.naziv
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE m.status = 'slobodan'
            LIMIT 1
            """
        )
    ).fetchone()
    if not row:
        return
    db.execute(text("UPDATE msisdn SET u_kvaru = true WHERE id = :id"), {"id": row.id})
    db.commit()
    ids = _find_slobodan_ids(db, row.naziv, 10)
    assert row.id not in ids
    db.execute(text("UPDATE msisdn SET u_kvaru = false WHERE id = :id"), {"id": row.id})
    db.commit()
