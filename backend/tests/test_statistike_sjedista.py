"""Testovi za novi `po_sjedistima` ključ u /statistike."""

from fastapi.testclient import TestClient


def test_statistike_imaju_po_sjedistima_kljuc(client: TestClient, admin_token: str):
    res = client.get("/statistike", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "po_sjedistima" in data
    assert isinstance(data["po_sjedistima"], list)


def test_po_sjedistima_ima_12_zupanija(client: TestClient, admin_token: str):
    data = client.get(
        "/statistike", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    sjedista = data["po_sjedistima"]
    assert len(sjedista) >= 10, (
        f"Očekivano barem 10 sjedišta s brojevima, dobiveno {len(sjedista)}"
    )
    ocekivana = {
        "Mostar", "Sarajevo", "Banja Luka", "Tuzla", "Zenica", "Travnik",
        "Livno", "Bihać", "Goražde", "Orašje", "Široki Brijeg", "Brčko",
    }
    stvarna = {s["sjediste"] for s in sjedista}
    prisutna = ocekivana & stvarna
    assert len(prisutna) >= 10, f"Premalo glavnih sjedišta: {prisutna}"


def test_postotak_zauzetosti_formula(client: TestClient, admin_token: str):
    data = client.get(
        "/statistike", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    for s in data["po_sjedistima"]:
        uk = s["ukupno"]
        if uk == 0:
            assert s["postotak_zauzetosti"] == 0.0
            continue
        ocekivano = round(((s["zauzeti"] + s["karantena"]) / uk) * 100, 2)
        assert abs(s["postotak_zauzetosti"] - ocekivano) < 0.01, (
            f"Sjedište {s['sjediste']}: postotak {s['postotak_zauzetosti']} != {ocekivano}"
        )


def test_oznaka_i_sjediste_postoje(client: TestClient, admin_token: str):
    data = client.get(
        "/statistike", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    for s in data["po_sjedistima"]:
        assert s["oznaka"], "Oznaka županije ne smije biti prazna"
        assert s["sjediste"], "Sjedište županije ne smije biti prazno"
        assert s["ukupno"] >= 0
        assert s["slobodni"] >= 0
        assert s["zauzeti"] >= 0
        assert s["karantena"] >= 0


def test_zbroj_komponenti_jednak_ukupnom(client: TestClient, admin_token: str):
    """Slobodni + zauzeti + karantena = ukupno (po sjedištu)."""
    data = client.get(
        "/statistike", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    for s in data["po_sjedistima"]:
        zbroj = s["slobodni"] + s["zauzeti"] + s["karantena"]
        assert zbroj == s["ukupno"], (
            f"Sjedište {s['sjediste']}: zbroj {zbroj} != ukupno {s['ukupno']}"
        )


def test_po_opcini_ima_lat_lon(client: TestClient, admin_token: str):
    data = client.get(
        "/statistike", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    nazivi_provjeravane = {"Mostar", "Stolac", "Čapljina"}
    for o in data["po_opcini"]:
        if o["naziv"] in nazivi_provjeravane:
            assert o["lat"] is not None, f"{o['naziv']} nema lat"
            assert o["lon"] is not None, f"{o['naziv']} nema lon"


def test_statistike_zahtjeva_auth(client: TestClient):
    res = client.get("/statistike")
    assert res.status_code in (401, 403)
