"""Generira fiksne brojeve HT Eronet (8 znamenki) prema stvarnim centralama.

Format MSISDN: NDC(2) + CENTRALA(3) + PRETPLATNIK(3) = 8 znamenki.

Stvarni primjeri iz HT mreže (verifikacija):
    Stolac    036 853 474, 036 854 432, 036 853 101
    Mostar    036 325 720, 036 336 821, 036 395 000
    Konjic    036 729 813, 036 735 370
    Čapljina  036 805 052, 036 805 060

Ukupno ≈ 600 000 brojeva, skalirano iz neskaliranog 2.234.000 plana.

CLI:
    python -m scripts.seed_inventar_fiksni --ukupno 600000
    python -m scripts.seed_inventar_fiksni --dry-run
    python -m scripts.seed_inventar_fiksni --ukupno 600000 --force-karantena
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.services.centrale_plan import (  # noqa: E402
    CENTRALE_PO_OPCINI,
    centrale_za,
    garantirane_za,
    skaliraj_centrale_na_target,
)
from app.services.kvaliteta_klasifikacija import klasificiraj_broj  # noqa: E402
from app.services.rak_geografija import (  # noqa: E402
    osiguraj_opcinu,
    slug_opcina,
    ucitaj_opcine_master,
)
from app.services.rak_import import (  # noqa: E402
    _get_or_create_lokacija,
    _get_or_create_raspon,
    _get_or_create_uredjaj,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed_inventar_fiksni")


def cisti_slobodne(db, force_karantena: bool) -> int:
    obrisano = 0
    res = db.execute(text("DELETE FROM msisdn WHERE status = 'slobodan'"))
    obrisano += res.rowcount or 0
    if force_karantena:
        res2 = db.execute(text("DELETE FROM msisdn WHERE status = 'karantena'"))
        obrisano += res2.rowcount or 0
    log.info("Obrisano MSISDN-a (slobodni/karantena): %s", obrisano)
    return obrisano


def cisti_prazne_lokacije(db) -> None:
    db.execute(
        text(
            """
            DELETE FROM rasponi WHERE NOT EXISTS (
                SELECT 1 FROM msisdn m WHERE m.raspon_id = rasponi.id
            )
            """
        )
    )
    db.execute(
        text(
            """
            DELETE FROM uredjaji WHERE NOT EXISTS (
                SELECT 1 FROM rasponi r WHERE r.uredjaj_id = uredjaji.id
            )
            """
        )
    )


def opcina_geo(opcina_naziv: str) -> tuple[str, str]:
    """Vrati (zupanija_oznaka, entitet) za općinu iz mastera."""
    for o in ucitaj_opcine_master():
        if o.naziv == opcina_naziv:
            return o.zupanija_oznaka, o.entitet
    if opcina_naziv == "Banja Luka":
        return "RS-BL", "RS"
    if opcina_naziv == "Brčko":
        return "BRC", "Brčko"
    return "HNŽ", "FBiH"


def generiraj(db, ukupno: int) -> dict:
    skala = skaliraj_centrale_na_target(ukupno)

    novi_brojevi = 0
    po_opcini: dict[str, int] = defaultdict(int)

    for opcina_naziv, broj_centrala_skalirano in skala.items():
        centrale_sve = centrale_za(opcina_naziv)
        if not centrale_sve:
            continue
        n_uzeti = min(broj_centrala_skalirano, len(centrale_sve))
        if n_uzeti <= 0:
            continue
        garantirane = garantirane_za(opcina_naziv)
        if n_uzeti >= len(centrale_sve):
            centrale_uzeti = list(centrale_sve)
        else:
            ostatak = [c for c in centrale_sve if c not in garantirane]
            preostalo = max(0, n_uzeti - len(garantirane))
            if preostalo > 0 and ostatak:
                korak = len(ostatak) / preostalo
                indeksi = sorted({int(i * korak) for i in range(preostalo)})
                izabrani = [ostatak[i] for i in indeksi if i < len(ostatak)]
            else:
                izabrani = []
            spojeno = list(garantirane) + izabrani
            poredak = {c: i for i, c in enumerate(centrale_sve)}
            centrale_uzeti = sorted(set(spojeno), key=lambda c: poredak[c])
        if not centrale_uzeti:
            continue

        zup_oznaka, entitet = opcina_geo(opcina_naziv)
        opcina_id = osiguraj_opcinu(db, opcina_naziv, zup_oznaka, entitet)
        lokacija_id = _get_or_create_lokacija(db, opcina_id, f"HT Eronet - {opcina_naziv}")

        for centrala in centrale_uzeti:
            uredjaj_id = _get_or_create_uredjaj(
                db,
                lokacija_id,
                f"MSAN-{centrala.ndc}-{centrala.prefiks}-{slug_opcina(opcina_naziv)}",
            )
            pocetak, kraj = centrala.pocetak(), centrala.kraj()
            raspon_id, _ = _get_or_create_raspon(db, uredjaj_id, pocetak, kraj)

            base = int(pocetak)
            db.execute(
                text(
                    """
                    INSERT INTO msisdn (broj, status, raspon_id, kvaliteta_id)
                    SELECT
                        LPAD((:base + g)::text, 8, '0'),
                        'slobodan',
                        :raspon_id,
                        (SELECT id FROM kvaliteta WHERE naziv = 'silver')
                    FROM generate_series(0, 999) AS g
                    ON CONFLICT (broj) DO NOTHING
                    """
                ),
                {"base": base, "raspon_id": raspon_id},
            )
            po_opcini[opcina_naziv] += 1000
            novi_brojevi += 1000

    db.commit()
    return {"novi_brojevi": novi_brojevi, "po_opcini": dict(po_opcini)}


def reklasificiraj_sve(db) -> int:
    """Postavi kvaliteta_id svakom MSISDN-u prema novoj klasifikaciji."""
    kvaliteta_id_po_nazivu = {
        row[0]: row[1]
        for row in db.execute(text("SELECT naziv, id FROM kvaliteta")).fetchall()
    }
    rows = db.execute(text("SELECT id, broj FROM msisdn WHERE status = 'slobodan'")).fetchall()
    updated = 0
    batch_size = 5000
    batch: list[tuple[int, int]] = []
    for r in rows:
        naziv = klasificiraj_broj(r.broj)
        kid = kvaliteta_id_po_nazivu[naziv]
        batch.append((r.id, kid))
        if len(batch) >= batch_size:
            for mid, k in batch:
                db.execute(
                    text("UPDATE msisdn SET kvaliteta_id = :k WHERE id = :id"),
                    {"k": k, "id": mid},
                )
            updated += len(batch)
            batch.clear()
    for mid, k in batch:
        db.execute(
            text("UPDATE msisdn SET kvaliteta_id = :k WHERE id = :id"),
            {"k": k, "id": mid},
        )
    updated += len(batch)
    db.commit()
    return updated


def dry_run(ukupno: int) -> None:
    skala = skaliraj_centrale_na_target(ukupno)
    ukupno_brojeva = sum(n * 1000 for n in skala.values())
    log.info("Ciljano %s; skalirani plan = %s brojeva", ukupno, ukupno_brojeva)
    log.info("Po općini (top 20):")
    top = sorted(skala.items(), key=lambda x: -x[1])[:20]
    for op, n in top:
        log.info("  %-22s centrale=%d brojeva=%d", op, n, n * 1000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ukupno", type=int, default=600_000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-karantena", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        dry_run(args.ukupno)
        return 0

    db = SessionLocal()
    try:
        cisti_slobodne(db, force_karantena=args.force_karantena)
        cisti_prazne_lokacije(db)
        db.commit()
        log.info("Generiranje brojeva...")
        rez = generiraj(db, args.ukupno)
        log.info("Reklasificiranje kvaliteta...")
        updated = reklasificiraj_sve(db)
        log.info("Reklasificirano: %s", updated)

        log.info("Novih brojeva: %s. Top 15 općina:", rez["novi_brojevi"])
        top = sorted(rez["po_opcini"].items(), key=lambda x: -x[1])[:15]
        for op, n in top:
            log.info("  %-22s %s", op, n)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
