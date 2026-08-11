"""Debug provjera fallbacka."""
from __future__ import annotations
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from sqlalchemy import text
from app.database import SessionLocal
from app.services.msisdn_service import _find_slobodan_ids

db = SessionLocal()
try:
    db.execute(text("INSERT INTO zupanije (oznaka, naziv, entitet, sjediste) VALUES ('TST','TestRegija','RS','Test') ON CONFLICT DO NOTHING"))
    db.execute(text("INSERT INTO opcine (naziv, zupanija_id, entitet) SELECT 'TestPraznaOpcina', id, 'RS' FROM zupanije WHERE oznaka='TST' ON CONFLICT DO NOTHING"))
    db.commit()

    zid = db.execute(text("SELECT zupanija_id FROM opcine WHERE naziv='TestPraznaOpcina'")).scalar()
    print("zupanija_id za TestPraznaOpcina:", zid)
    cnt = db.execute(text("SELECT COUNT(*) FROM opcine WHERE zupanija_id=:z"), {"z": zid}).scalar()
    print("broj opcina u zupaniji:", cnt)
    cnt_m = db.execute(text("""
        SELECT COUNT(*) FROM msisdn m
        JOIN rasponi r ON r.id = m.raspon_id
        JOIN uredjaji u ON u.id = r.uredjaj_id
        JOIN lokacije l ON l.id = u.lokacija_id
        JOIN opcine o ON o.id = l.opcina_id
        WHERE o.zupanija_id = :z
    """), {"z": zid}).scalar()
    print("msisdn u toj zupaniji:", cnt_m)

    ids = _find_slobodan_ids(db, 'TestPraznaOpcina', 1)
    print("vraceno IDs:", ids)
finally:
    db.execute(text("DELETE FROM opcine WHERE naziv='TestPraznaOpcina'"))
    db.execute(text("DELETE FROM zupanije WHERE oznaka='TST'"))
    db.commit()
    db.close()
