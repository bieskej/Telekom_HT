"""Testovi za GET /opcine/geojson endpoint (choropleth podaci)."""

from fastapi.testclient import TestClient


def _opcine_iz_statistike(client: TestClient, token: str) -> set[str]:
    res = client.get("/statistike", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    return {o["naziv"] for o in res.json()["po_opcini"]}


def test_geojson_vraca_feature_collection(client: TestClient, admin_token: str):
    res = client.get(
        "/opcine/geojson", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)
    assert len(data["features"]) > 0
    first = data["features"][0]
    assert first["type"] == "Feature"
    assert first["geometry"]["type"] == "Polygon"
    props = first["properties"]
    for key in ("naziv", "ukupno", "slobodni", "postotak_zauzetosti", "lat", "lon"):
        assert key in props, f"GeoJSON properties nemaju ključ {key}"


def test_geojson_sadrzi_sve_opcine_iz_statistike(client: TestClient, admin_token: str):
    geojson_opcine = {
        f["properties"]["naziv"]
        for f in client.get(
            "/opcine/geojson", headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["features"]
    }
    statistika_opcine = _opcine_iz_statistike(client, admin_token)
    nedostaju = statistika_opcine - geojson_opcine
    assert not nedostaju, f"Općine bez geo podataka: {nedostaju}"


def test_geojson_postotak_unutar_0_100(client: TestClient, admin_token: str):
    data = client.get(
        "/opcine/geojson", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    for feat in data["features"]:
        p = feat["properties"]["postotak_zauzetosti"]
        assert 0.0 <= p <= 100.0, f"Neispravan postotak {p} za {feat['properties']['naziv']}"


def test_geojson_zahtjeva_auth(client: TestClient):
    res = client.get("/opcine/geojson")
    assert res.status_code in (401, 403)


def test_geojson_polygon_zatvoren_prsten(client: TestClient, admin_token: str):
    data = client.get(
        "/opcine/geojson", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    for feat in data["features"]:
        ring = feat["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1], f"Polygon prsten nije zatvoren za {feat['properties']['naziv']}"
        assert len(ring) >= 4, "Polygon mora imati minimalno 4 točke (3 + zatvarač)"


def test_geojson_kljucne_opcine_prisutne(client: TestClient, admin_token: str):
    nazivi = {
        f["properties"]["naziv"]
        for f in client.get(
            "/opcine/geojson", headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["features"]
    }
    for op in ("Mostar", "Stolac", "Čapljina", "Neum", "Sarajevo", "Banja Luka", "Brčko"):
        assert op in nazivi, f"Općina {op} mora biti na mapi"
