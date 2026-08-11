"""Jednokratno čišćenje praznih duplikata općina (Brčko u KS, Banja Luka u SBŽ)."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402

PARI = [
    ("Brčko", "KS"),
    ("Banja Luka", "SBŽ"),
]


def main() -> int:
    db = SessionLocal()
    obr_lok = 0
    obr_opc = 0
    try:
        for naziv, zup in PARI:
            opc_id = db.execute(
                text(
                    """
                    SELECT o.id FROM opcine o
                    JOIN zupanije z ON z.id = o.zupanija_id
                    WHERE o.naziv = :n AND z.oznaka = :z
                    """
                ),
                {"n": naziv, "z": zup},
            ).scalar()
            if not opc_id:
                continue
            ima_msisdn = db.execute(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM lokacije l
                        JOIN uredjaji u ON u.lokacija_id = l.id
                        JOIN rasponi r ON r.uredjaj_id = u.id
                        JOIN msisdn m ON m.raspon_id = r.id
                        WHERE l.opcina_id = :id
                    )
                    """
                ),
                {"id": int(opc_id)},
            ).scalar()
            if ima_msisdn:
                print(f"Preskačem (ima MSISDN): {naziv} / {zup} (id={opc_id})")
                continue
            res = db.execute(
                text("DELETE FROM lokacije WHERE opcina_id = :id"),
                {"id": int(opc_id)},
            )
            obr_lok += res.rowcount or 0
            res2 = db.execute(text("DELETE FROM opcine WHERE id = :id"), {"id": int(opc_id)})
            obr_opc += res2.rowcount or 0
            print(f"Obrisano: {naziv} / {zup} (id={opc_id})")
        db.commit()
        print(f"Ukupno obrisano lokacija={obr_lok} opcina={obr_opc}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
