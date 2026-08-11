"""Test SMTP: /test-email i dodjela s emailom."""
import sys

import requests

BASE = "http://127.0.0.1:8002"
EMAIL = "lebony.br@gmail.com"
VALID_JMBG = "0101000500012"


def login() -> str:
    r = requests.post(
        f"{BASE}/prijava",
        json={"email": "admin@eronet.ba", "lozinka": "admin"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def test_email(token: str) -> dict:
    r = requests.post(
        f"{BASE}/test-email",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_email": EMAIL},
        timeout=60,
    )
    print("=== POST /test-email ===")
    print("Status:", r.status_code)
    print("Body:", r.text)
    r.raise_for_status()
    return r.json()


def test_dodjela(token: str) -> dict:
    r = requests.post(
        f"{BASE}/dodijeli-broj",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "opcina_naziv": "Mostar",
            "ime": "Test",
            "prezime": "Korisnik",
            "jmbg": VALID_JMBG,
            "email": EMAIL,
            "kvaliteta_id": None,
        },
        timeout=60,
    )
    print("\n=== POST /dodijeli-broj ===")
    print("Status:", r.status_code)
    print("Body:", r.text)
    r.raise_for_status()
    return r.json()


def verify_pdf() -> None:
    from app.services.invoice_email import generiraj_pdf_racun

    pdf = generiraj_pdf_racun(
        "Test", "Korisnik", VALID_JMBG, EMAIL, "+387 61 000 000", "silver", 10.0
    )
    assert pdf.startswith(b"%PDF")
    text = pdf.decode("latin-1", errors="ignore")
    checks = [
        ("HT Eronet" in text or "HT Eronet" in repr(pdf), "zaglavlje"),
        (b"Test" in pdf and b"Korisnik" in pdf, "ime/prezime"),
    ]
    from pathlib import Path

    potpis = Path(__file__).resolve().parents[1] / "assets" / "potpis.png"
    print("\n=== PDF provjera (lokalno) ===")
    print("Velicina PDF:", len(pdf), "bajtova")
    print("potpis.png postoji:", potpis.exists())
    for ok, label in checks:
        print(f"  {label}: {'OK' if ok else 'NE'}")


def main() -> None:
    from app.config import settings

    if not settings.smtp_password:
        print("GRESKA: SMTP_PASSWORD je prazan u backend/.env")
        print("Dodaj Gmail App Password i ponovo pokreni backend.")
        sys.exit(1)

    token = login()
    res = test_email(token)
    if not res.get("poslano"):
        print("\nEmail NIJE poslan:", res.get("poruka"))
        sys.exit(1)

    verify_pdf()
    dod = test_dodjela(token)
    print("\nDodjela email_poslan:", dod.get("email_poslan"))
    print("\nUSPJEH: test email i dodjela pozvani. Provjeri inbox:", EMAIL)


if __name__ == "__main__":
    main()
