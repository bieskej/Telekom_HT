import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal
from app.main import app
from app.services.jmbg import validiraj_jmbg


def generiraj_validan_jmbg(dan: str = "01", mjesec: str = "01", godina: str = "000", regija: str = "50", serijski: str = "001") -> str:
    """Generira validan JMBG za testove (bez kontrolne znamenke pa je izračuna)."""
    baza = f"{dan}{mjesec}{godina}{regija}{serijski}"
    weights = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    total = sum(int(baza[i]) * weights[i] for i in range(12))
    remainder = total % 11
    kontrolna = 11 - remainder
    if kontrolna in (10, 11):
        kontrolna = 0
    jmbg = baza + str(kontrolna)
    assert validiraj_jmbg(jmbg)
    return jmbg


VALID_JMBG = generiraj_validan_jmbg()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client: TestClient) -> str:
    res = client.post("/prijava", json={"email": "admin@eronet.ba", "lozinka": "admin"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def _migrate_notifikacije_status():
    db = SessionLocal()
    try:
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        migrate_sql = (scripts_dir / "migrate_adresa_placanja.sql").read_text(encoding="utf-8")
        posta_sql = (scripts_dir / "migrate_posta_hijerarhija.sql").read_text(encoding="utf-8")
        for stmt in migrate_sql.split(";"):
            s = stmt.strip()
            if s:
                db.execute(text(s))
        for stmt in posta_sql.split(";"):
            s = stmt.strip()
            if s and not s.startswith("--"):
                db.execute(text(s))
        db.execute(text("ALTER TABLE notifikacije DROP CONSTRAINT IF EXISTS notifikacije_status_check"))
        db.execute(
            text(
                """
                ALTER TABLE notifikacije ADD CONSTRAINT notifikacije_status_check
                CHECK (status IN ('ceka', 'poslano', 'greska', 'nedostaje_smtp'))
                """
            )
        )
        db.execute(text("ALTER TABLE notifikacije ADD COLUMN IF NOT EXISTS tip VARCHAR(50)"))
        db.execute(text("ALTER TABLE radnici ADD COLUMN IF NOT EXISTS jmbg VARCHAR(13)"))
        db.execute(text("ALTER TABLE radnici DROP CONSTRAINT IF EXISTS radnici_uloga_check"))
        db.execute(
            text(
                """
                ALTER TABLE radnici ADD CONSTRAINT radnici_uloga_check
                CHECK (uloga IN ('admin', 'prodaja', 'promet', 'kupac'))
                """
            )
        )
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS kupac_kontakt (
                    id SERIAL PRIMARY KEY,
                    kupac_id INTEGER NOT NULL REFERENCES radnici(id),
                    predmet VARCHAR(255) NOT NULL,
                    poruka TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )
        )
        db.execute(text("ALTER TABLE msisdn ADD COLUMN IF NOT EXISTS karantena_razlog VARCHAR(255)"))
        db.execute(
            text(
                "ALTER TABLE msisdn ADD COLUMN IF NOT EXISTS u_kvaru BOOLEAN NOT NULL DEFAULT false"
            )
        )
        db.execute(text("ALTER TABLE msisdn DROP CONSTRAINT IF EXISTS msisdn_status_check"))
        db.execute(
            text(
                """
                ALTER TABLE msisdn ADD CONSTRAINT msisdn_status_check
                CHECK (status IN ('slobodan', 'zauzet', 'karantena', 'portano'))
                """
            )
        )
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS portabilnost (
                    id SERIAL PRIMARY KEY,
                    msisdn_id INTEGER REFERENCES msisdn(id),
                    broj VARCHAR(15),
                    tip VARCHAR(20) NOT NULL,
                    izvor_op VARCHAR(100) NOT NULL,
                    ciljni_op VARCHAR(100) NOT NULL,
                    datum_zahtjeva TIMESTAMPTZ DEFAULT now(),
                    datum_realizacije TIMESTAMPTZ,
                    status VARCHAR(30) NOT NULL DEFAULT 'zahtjev',
                    napomena TEXT,
                    created_by INTEGER REFERENCES radnici(id)
                )
                """
            )
        )
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS servisni_nalog (
                    id SERIAL PRIMARY KEY,
                    uredjaj_id INTEGER NOT NULL REFERENCES uredjaji(id),
                    opis TEXT NOT NULL,
                    status VARCHAR(30) NOT NULL DEFAULT 'otvoren',
                    prioritet VARCHAR(20) NOT NULL DEFAULT 'srednji',
                    prijavio_id INTEGER REFERENCES radnici(id),
                    rijesio_id INTEGER REFERENCES radnici(id),
                    created_at TIMESTAMPTZ DEFAULT now(),
                    rijeseno_at TIMESTAMPTZ
                )
                """
            )
        )
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS email_log (
                    id SERIAL PRIMARY KEY,
                    msisdn_id INTEGER REFERENCES msisdn(id),
                    primatelj VARCHAR(255) NOT NULL,
                    predmet VARCHAR(500) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_text TEXT,
                    html_tijelo TEXT,
                    sent_at TIMESTAMPTZ
                )
                """
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def slobodan_broj_mostar(db):
    """Pronađi jedan slobodan broj u Mostaru i vrati ga; ako nema, preskoči test."""
    row = db.execute(
        text(
            """
            SELECT m.id, m.broj
            FROM msisdn m
            JOIN rasponi r ON r.id = m.raspon_id
            JOIN uredjaji u ON u.id = r.uredjaj_id
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE o.naziv = 'Mostar'
              AND m.status = 'slobodan'
              AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
              AND k.naziv = 'silver'
            ORDER BY m.broj
            LIMIT 1
            """
        )
    ).fetchone()
    return row
