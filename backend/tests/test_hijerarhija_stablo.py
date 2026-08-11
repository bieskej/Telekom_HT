"""Testovi za endpoint /hijerarhija/stablo i /hijerarhija/cvor.

Master-detail prikaz na stranici `/hijerarhija`: cijelo stablo
Županija → Općina → Lokacija → MSAN s MSISDN brojanjem.
"""
from fastapi.testclient import TestClient


def test_stablo_ima_zupanije_opcine_lokacije_msan(client: TestClient, admin_token: str):
    res = client.get(
        "/hijerarhija/stablo",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Stablo mora imati barem jednu županiju"

    zup = data[0]
    assert zup["tip"] == "zupanija"
    assert "id" in zup and "naziv" in zup and "oznaka" in zup
    assert zup["ukupno"] > 0
    assert len(zup["opcine"]) > 0

    op = zup["opcine"][0]
    assert op["tip"] == "opcina"
    assert "id" in op and "naziv" in op
    assert len(op["lokacije"]) > 0

    lok = op["lokacije"][0]
    assert lok["tip"] == "lokacija"
    assert len(lok["uredjaji"]) > 0

    ur = lok["uredjaji"][0]
    assert ur["tip"] == "uredjaj"
    assert "uredjaj_tip" in ur
    assert ur["ukupno"] > 0


def test_counts_se_poklapaju_sa_statistikom(client: TestClient, admin_token: str):
    """Zbroj ukupnih MSISDN-a iz stabla mora odgovarati `/statistike.ukupno`."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    stablo = client.get("/hijerarhija/stablo", headers=headers).json()
    stat = client.get("/statistike", headers=headers).json()

    stablo_ukupno = sum(z["ukupno"] for z in stablo)
    assert stablo_ukupno == stat["ukupno"], (
        f"Stablo ukupno={stablo_ukupno}, statistike.ukupno={stat['ukupno']}"
    )

    for z in stablo:
        suma_opcina = sum(o["ukupno"] for o in z["opcine"])
        assert suma_opcina == z["ukupno"], (
            f"Županija {z['naziv']}: zbroj općina {suma_opcina} ≠ {z['ukupno']}"
        )
        for o in z["opcine"]:
            suma_lokacija = sum(l["ukupno"] for l in o["lokacije"])
            assert suma_lokacija == o["ukupno"]
            for l in o["lokacije"]:
                suma_uredjaja = sum(u["ukupno"] for u in l["uredjaji"])
                assert suma_uredjaja == l["ukupno"]


def test_stablo_grane_imaju_msisdn(client: TestClient, admin_token: str):
    """Stablo vraća samo grane koje sadrže barem jedan MSISDN
    (ne smije biti čvora s ukupno=0)."""
    res = client.get(
        "/hijerarhija/stablo",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    data = res.json()
    for z in data:
        assert z["ukupno"] > 0
        for o in z["opcine"]:
            assert o["ukupno"] > 0
            for l in o["lokacije"]:
                assert l["ukupno"] > 0
                for u in l["uredjaji"]:
                    assert u["ukupno"] > 0


def test_cvor_opcina_vraca_detalj(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    stablo = client.get("/hijerarhija/stablo", headers=headers).json()
    opcina_id = None
    for z in stablo:
        for o in z["opcine"]:
            if o["naziv"] == "Stolac":
                opcina_id = o["id"]
                break
        if opcina_id:
            break
    assert opcina_id is not None, "Stolac mora biti u stablu"

    res = client.get(
        f"/hijerarhija/cvor?tip=opcina&id={opcina_id}",
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["tip"] == "opcina"
    assert body["naslov"] == "Stolac"
    assert body["metrike"]["ukupno"] > 0
    assert body["filter_param"]["kljuc"] == "opcina_naziv"
    assert body["filter_param"]["vrijednost"] == "Stolac"


def test_cvor_uredjaj_vraca_uzorak_brojeva(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    stablo = client.get("/hijerarhija/stablo", headers=headers).json()
    uredjaj_id = stablo[0]["opcine"][0]["lokacije"][0]["uredjaji"][0]["id"]

    res = client.get(
        f"/hijerarhija/cvor?tip=uredjaj&id={uredjaj_id}",
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["tip"] == "uredjaj"
    assert body["metrike"]["ukupno"] > 0
    assert len(body["brojevi_uzorak"]) <= 10
    if body["brojevi_uzorak"]:
        b = body["brojevi_uzorak"][0]
        assert "broj" in b and "status" in b and "kvaliteta" in b
    assert body["filter_param"] is not None
    assert body["filter_param"]["kljuc"] == "uredjaj_id"


def test_cvor_nepostojeci_404(client: TestClient, admin_token: str):
    res = client.get(
        "/hijerarhija/cvor?tip=uredjaj&id=999999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404


def test_cvor_neispravan_tip_422(client: TestClient, admin_token: str):
    res = client.get(
        "/hijerarhija/cvor?tip=nesto&id=1",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 422


def test_stablo_zahtjeva_autentifikaciju(client: TestClient):
    res = client.get("/hijerarhija/stablo")
    assert res.status_code in (401, 403)
