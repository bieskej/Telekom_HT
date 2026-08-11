#!/usr/bin/env python3
"""
Reklasifikacija msisdn.kvaliteta_id prema uzorku broja (kvaliteta_klasifikacija).

Primjeri:
  python scripts/reklasificiraj_kvalitete.py --dry-run
  python scripts/reklasificiraj_kvalitete.py
  python scripts/reklasificiraj_kvalitete.py --svi
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import bindparam, text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal  # noqa: E402
from app.services.kvaliteta_klasifikacija import klasificiraj_broj  # noqa: E402

BATCH_SIZE = 500


def _ucitaj_kvaliteta_ids(db) -> dict[str, int]:
    return {naziv: kid for naziv, kid in db.execute(text("SELECT naziv, id FROM kvaliteta")).fetchall()}


def _where_samo_slobodan() -> str:
    return """
        status = 'slobodan'
        AND (rezerviran_do IS NULL OR rezerviran_do < NOW())
    """


def _statistika(db) -> Counter[str]:
    rows = db.execute(
        text(
            """
            SELECT k.naziv, COUNT(*)::int
            FROM msisdn m
            JOIN kvaliteta k ON k.id = m.kvaliteta_id
            GROUP BY k.naziv
            ORDER BY k.naziv
            """
        )
    ).fetchall()
    return Counter({naziv: cnt for naziv, cnt in rows})


def _ispisi_statistiku(naslov: str, stats: Counter[str]) -> None:
    print(naslov)
    ukupno = sum(stats.values())
    for naziv in ("diamond", "platinum", "gold", "silver"):
        cnt = stats.get(naziv, 0)
        postotak = (100.0 * cnt / ukupno) if ukupno else 0.0
        print(f"  {naziv:9} {cnt:6} ({postotak:5.2f}%)")
    print(f"  {'ukupno':9} {ukupno:6}")


def _primijeni_migraciju_indeksa(db) -> None:
    sql_path = Path(__file__).resolve().parent / "migrate_msisdn_kvaliteta_index.sql"
    db.execute(text(sql_path.read_text(encoding="utf-8")))
    db.commit()
    print("Indeks idx_msisdn_kvaliteta_status provjeren/kreiran.")


def reklasificiraj(
    dry_run: bool,
    samo_slobodan: bool,
    primijeni_indeks: bool,
) -> int:
    db = SessionLocal()
    try:
        if primijeni_indeks:
            _primijeni_migraciju_indeksa(db)

        kvaliteta_ids = _ucitaj_kvaliteta_ids(db)
        where = _where_samo_slobodan() if samo_slobodan else "TRUE"
        opis = "slobodni (bez aktivne rezervacije)" if samo_slobodan else "svi brojevi"

        prije = _statistika(db)
        _ispisi_statistiku(f"\nStanje prije ({opis}):", prije)

        azurirano = 0
        promjene_po_kvaliteti: Counter[str] = Counter()
        last_id = 0

        while True:
            rows = db.execute(
                text(
                    f"""
                    SELECT id, broj, kvaliteta_id
                    FROM msisdn
                    WHERE id > :last_id AND {where}
                    ORDER BY id
                    LIMIT :limit
                    """
                ),
                {"last_id": last_id, "limit": BATCH_SIZE},
            ).fetchall()
            if not rows:
                break

            batch_updates: dict[int, list[int]] = {}
            for msisdn_id, broj, stari_kid in rows:
                last_id = msisdn_id
                novi_naziv = klasificiraj_broj(broj)
                novi_kid = kvaliteta_ids[novi_naziv]
                if stari_kid == novi_kid:
                    continue
                batch_updates.setdefault(novi_kid, []).append(msisdn_id)
                promjene_po_kvaliteti[novi_naziv] += 1

            if not dry_run and batch_updates:
                update_sql = (
                    text(
                        """
                        UPDATE msisdn
                        SET kvaliteta_id = :kid, updated_at = NOW()
                        WHERE id IN :ids
                        """
                    ).bindparams(bindparam("ids", expanding=True))
                )
                for novi_kid, id_list in batch_updates.items():
                    db.execute(update_sql, {"kid": novi_kid, "ids": id_list})
                    azurirano += len(id_list)
                db.commit()
            elif dry_run:
                azurirano += sum(len(v) for v in batch_updates.values())

        poslije = _statistika(db)
        _ispisi_statistiku(f"\nStanje poslije (cijela baza):", poslije)

        mod = "DRY-RUN" if dry_run else "AŽURIRANO"
        print(f"\n{mod}: {azurirano} brojeva bi promijenilo kvalitetu ({opis}).")
        if promjene_po_kvaliteti:
            print("Promjene po novoj kvaliteti:")
            for naziv, cnt in promjene_po_kvaliteti.most_common():
                print(f"  -> {naziv}: {cnt}")

        return 0
    except Exception as exc:
        db.rollback()
        print(f"Greška: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reklasifikacija MSISDN kvaliteta po uzorku broja.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Samo statistika i broj promjena, bez UPDATE-a.",
    )
    parser.add_argument(
        "--svi",
        action="store_true",
        help="Ažuriraj i zauzete/karantena brojeve (oprezno). Zadano: samo slobodni.",
    )
    parser.add_argument(
        "--indeks",
        action="store_true",
        help="Primijeni migrate_msisdn_kvaliteta_index.sql prije reklasifikacije.",
    )
    args = parser.parse_args()
    samo_slobodan = not args.svi
    sys.exit(reklasificiraj(args.dry_run, samo_slobodan, args.indeks))


if __name__ == "__main__":
    main()
