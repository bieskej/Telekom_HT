from pathlib import Path

from fastapi.testclient import TestClient

from app.services.postanski_import import import_postanski_uredi

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "postanski_sample.csv"


def test_hijerarhija_tree(client: TestClient, admin_token: str, db):
    import_postanski_uredi(db, FIXTURE)
    res = client.get("/hijerarhija/tree", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert any(g["entitet"] == "FBiH" for g in data)
    fbih = next(g for g in data if g["entitet"] == "FBiH")
    assert len(fbih["zupanije"]) >= 1


def test_hijerarhija_opcina_detail(client: TestClient, admin_token: str, db):
    import_postanski_uredi(db, FIXTURE)
    tree = client.get("/hijerarhija/tree", headers={"Authorization": f"Bearer {admin_token}"}).json()
    opcina_id = None
    for g in tree:
        for z in g["zupanije"]:
            for o in z["opcine"]:
                if o["naziv"] == "Stolac":
                    opcina_id = o["id"]
                    break
    assert opcina_id is not None
    res = client.get(
        f"/hijerarhija/opcina/{opcina_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["opcina"]["naziv"] == "Stolac"
    assert any(p["postanski_broj"] == "88360" for p in body["postanski_uredi"])


def test_hijerarhija_pretraga_pb(client: TestClient, admin_token: str, db):
    import_postanski_uredi(db, FIXTURE)
    res = client.get(
        "/hijerarhija/pretraga?pb=88360",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["opcina_naziv"] == "Stolac"


def test_import_postanski_admin_endpoint(client: TestClient, admin_token: str):
    res = client.post(
        "/admin/import-postanski-uredi",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert res.status_code == 200
    assert "ukupno" in res.json()
