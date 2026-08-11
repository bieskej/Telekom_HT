"""Jednokratni cleanup testne TST županije / općine."""
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
db.execute(text("DELETE FROM opcine WHERE naziv='TestOpcinaBezBrojeva'"))
db.execute(text("DELETE FROM opcine WHERE naziv='TestPraznaOpcina'"))
db.execute(text("DELETE FROM opcine WHERE naziv='TestPraznaOpcina2'"))
db.execute(text("DELETE FROM zupanije WHERE oznaka='TST'"))
db.commit()
print("Cleanup OK")
db.close()
