"""Test importa RAK CSV-a – novi + postojeći blok."""
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8002"
CSV_PATH = Path(__file__).resolve().parent / "test_new_block.csv"

CSV_CONTENT = """RAK izvještaj - test
HT Eronet
Dodijeljeni blokovi
,,,,
,,,,
,,,,
NDC,Blok,Duzina,,Operator,
31,3199,8,,HT d.d. Mostar,
30,3049,8,,HT d.d. Mostar,
"""


def main() -> None:
    CSV_PATH.write_text(CSV_CONTENT, encoding="utf-8-sig")
    print(f"Zapisano: {CSV_PATH}")

    login = requests.post(
        f"{BASE_URL}/prijava",
        json={"email": "admin@eronet.ba", "lozinka": "admin"},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    print("Prijava OK")

    with CSV_PATH.open("rb") as f:
        res = requests.post(
            f"{BASE_URL}/admin/import-rak",
            headers={"Authorization": f"Bearer {token}"},
            files={"datoteka": ("test_new_block.csv", f, "text/csv")},
            timeout=120,
        )

    print(f"Status: {res.status_code}")
    print(f"Odgovor: {res.text}")

    if res.status_code != 200:
        raise SystemExit(1)

    data = res.json()
    expected = {
        "novi_rasponi": 1,
        "novi_brojevi": 100,
        "preskoceni": 100,
        "obradeno_blokova": 2,
    }
    print("\nOcekivano vs stvarno:")
    ok = True
    for key, exp in expected.items():
        got = data.get(key)
        match = got == exp
        print(f"  {key}: {got} (ocekivano {exp}) {'OK' if match else 'NE'}")
        if not match:
            ok = False

    if ok:
        print("\nTest importa novog bloka uspjesan")
    else:
        print("\nTest NIJE prosao")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
