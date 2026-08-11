"""Debug POST /dodijeli-broj za praznu općinu."""
from __future__ import annotations
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import SessionLocal

VALID_JMBG = "0101000500017"
db = SessionLocal()
client = TestClient(app)

db.execute(text("INSERT INTO zupanije (oznaka, naziv, entitet, sjediste) VALUES ('TST','TestRegija','RS','Test') ON CONFLICT DO NOTHING"))
db.execute(text("INSERT INTO opcine (naziv, zupanija_id, entitet) SELECT 'TestPraznaOpcina2', id, 'RS' FROM zupanije WHERE oznaka='TST' ON CONFLICT DO NOTHING"))
db.commit()

login = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
token = login.json()["access_token"]

# Generiraj validan JMBG
from tests.conftest import generiraj_validan_jmbg
JMBG = generiraj_validan_jmbg()
print("JMBG:", JMBG)

resp = client.post(
    "/dodijeli-broj",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "opcina_naziv": "TestPraznaOpcina2",
        "ime": "Test",
        "prezime": "Korisnik",
        "jmbg": JMBG,
        "email": "test@example.com",
        "adresa": "Test 1",
        "grad": "Mostar",
        "postanski_broj": "88000",
    },
)
print("Status:", resp.status_code)
print("Body:", resp.json())

db.execute(text("DELETE FROM opcine WHERE naziv='TestPraznaOpcina2'"))
db.execute(text("DELETE FROM zupanije WHERE oznaka='TST'"))
db.commit()
db.close()
