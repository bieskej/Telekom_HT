"""Generira ~150.000 MSISDN-a proporcionalno populaciji po općini.

Format broja: 9 znamenki (E.164 N(S)N max). Struktura:
    NDC(2) + SLOT(3) + SN(4)

Svaka općina dobiva jedan ili više slot-ova, svaki slot = 10.000 brojeva
(`f"{ndc}{slot:03d}{0000-9999}"`). Slot ID-ovi su jedinstveni po NDC-u, pa
nema preklapanja brojeva među općinama.

NDC alokacija po entitetu/županiji:
    HNŽ → 63 (primarni), 36 i 64 kao backup
    ZHŽ → 39
    HBŽ → 34
    KS  → 33
    TK  → 35
    ZDŽ → 32
    SBŽ → 30
    BPŽ → 38
    USŽ → 37
    ŽP  → 31
    BRC → 49
    RS-BL (Banja Luka) → 51

Sigurnost:
- Slobodne MSISDN-e BRIŠE; zauzete/karantena NE BRIŠE (osim s `--force-karantena`).
- Zauzete brojeve uvijek čuva (regulativa naloga: ne brisati aktivne korisnike).

CLI:
    python -m scripts.seed_inventar --ukupno 150000
    python -m scripts.seed_inventar --ukupno 200000 --force-karantena
    python -m scripts.seed_inventar --dry-run
"""
from __future__ import annotations

import argparse
import logging
import math
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.services.kvaliteta_klasifikacija import klasificiraj_broj  # noqa: E402
from app.services.populacija import POPULACIJA, izracunaj_kvote  # noqa: E402
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
log = logging.getLogger("seed_inventar")

NDC_PO_ZUPANIJI: dict[str, str] = {
    "HNŽ": "63",
    "ZHŽ": "39",
    "HBŽ": "34",
    "KS": "33",
    "TK": "35",
    "ZDŽ": "32",
    "SBŽ": "30",
    "BPŽ": "38",
    "USŽ": "37",
    "ŽP": "31",
    "BRC": "49",
    "RS-BL": "51",
}

SLOT_SIZE = 10_000


def cisti_slobodne(db, force_karantena: bool) -> int:
    obrisano = 0
    res = db.execute(text("DELETE FROM msisdn WHERE status = 'slobodan'"))
    obrisano += res.rowcount or 0
    if force_karantena:
        res2 = db.execute(text("DELETE FROM msisdn WHERE status = 'karantena'"))
        obrisano += res2.rowcount or 0
    log.info("Obrisano MSISDN-a (slobodni/karantena): %s", obrisano)
    return obrisano


def cisti_prazne_lokacije(db) -> int:
    res = db.execute(
        text(
            """
            DELETE FROM rasponi WHERE NOT EXISTS (
                SELECT 1 FROM msisdn m WHERE m.raspon_id = rasponi.id
            )
            """
        )
    )
    obr_rasp = res.rowcount or 0
    res2 = db.execute(
        text(
            """
            DELETE FROM uredjaji WHERE NOT EXISTS (
                SELECT 1 FROM rasponi r WHERE r.uredjaj_id = uredjaji.id
            )
            """
        )
    )
    obr_ur = res2.rowcount or 0
    log.info("Obrisano praznih raspona=%s uređaja=%s", obr_rasp, obr_ur)
    return obr_rasp + obr_ur


def aktivne_opcine_iz_mastera() -> list[tuple[str, str, str]]:
    master = ucitaj_opcine_master()
    out: list[tuple[str, str, str]] = []
    for o in master:
        if o.zupanija_oznaka not in NDC_PO_ZUPANIJI:
            if o.naziv == "Banja Luka":
                out.append((o.naziv, "RS-BL", "RS"))
            continue
        out.append((o.naziv, o.zupanija_oznaka, o.entitet))
    if not any(n == "Banja Luka" for n, _, _ in out):
        out.append(("Banja Luka", "RS-BL", "RS"))
    if not any(n == "Brčko" for n, _, _ in out):
        out.append(("Brčko", "BRC", "Brčko"))
    return out


def generiraj(db, ukupno: int) -> dict:
    opcine = aktivne_opcine_iz_mastera()
    nazivi = [n for n, _, _ in opcine]
    kvote = izracunaj_kvote(nazivi, ukupno)

    kvaliteta_ids = {
        row[0]: row[1]
        for row in db.execute(text("SELECT naziv, id FROM kvaliteta")).fetchall()
    }
    slot_po_ndc: dict[str, int] = defaultdict(int)
    generirano_po_opcini: dict[str, int] = defaultdict(int)
    ukupno_generirano = 0

    for naziv, zup_oznaka, entitet in opcine:
        ndc = NDC_PO_ZUPANIJI.get(zup_oznaka)
        if not ndc:
            continue
        kvota = kvote.get(naziv, 0)
        if kvota <= 0:
            continue

        broj_slotova = max(1, math.ceil(kvota / SLOT_SIZE))
        preostalo = kvota
        opcina_id = osiguraj_opcinu(db, naziv, zup_oznaka, entitet)
        lokacija_id = _get_or_create_lokacija(db, opcina_id, f"HT Eronet - {naziv}")

        for _ in range(broj_slotova):
            slot = slot_po_ndc[ndc]
            slot_po_ndc[ndc] += 1
            if slot > 999:
                log.warning("Slotovi NDC=%s iscrpljeni za %s.", ndc, naziv)
                break
            uzeto = min(preostalo, SLOT_SIZE)
            pocetak = f"{ndc}{slot:03d}0000"
            kraj = f"{ndc}{slot:03d}{uzeto - 1:04d}"
            uredjaj_id = _get_or_create_uredjaj(
                db,
                lokacija_id,
                f"MSAN-{ndc}-{slot:03d}-{slug_opcina(naziv)}",
            )
            raspon_id, _ = _get_or_create_raspon(db, uredjaj_id, pocetak, kraj)
            ins_sql = text(
                """
                INSERT INTO msisdn (broj, status, raspon_id, kvaliteta_id)
                SELECT
                    LPAD((:base + g)::text, 9, '0'),
                    'slobodan',
                    :raspon_id,
                    (SELECT id FROM kvaliteta WHERE naziv = 'silver')
                FROM generate_series(0, :n - 1) AS g
                ON CONFLICT (broj) DO NOTHING
                """
            )
            base = int(pocetak)
            db.execute(
                ins_sql,
                {"base": base, "raspon_id": raspon_id, "n": uzeto},
            )
            generirano_po_opcini[naziv] += uzeto
            ukupno_generirano += uzeto
            preostalo -= uzeto
            if preostalo <= 0:
                break

    log.info("Refresh kvaliteta po uzorku znamenki...")
    db.execute(
        text(
            """
            UPDATE msisdn m
            SET kvaliteta_id = k.id
            FROM kvaliteta k
            WHERE k.naziv = CASE
                WHEN m.broj ~ '^([0-9])\\1{8}$' THEN 'diamond'
                WHEN m.broj ~ '([0-9])\\1{3,}' THEN 'platinum'
                WHEN m.broj ~ '([0-9])\\1{2}' OR m.broj ~ '012|123|234|345|456|567|678|789' THEN 'gold'
                ELSE 'silver'
            END
              AND m.kvaliteta_id IS DISTINCT FROM k.id
              AND m.status = 'slobodan'
            """
        )
    )
    db.commit()

    return {
        "ukupno_generirano": ukupno_generirano,
        "po_opcini": dict(generirano_po_opcini),
        "broj_opcina": len([n for n, v in generirano_po_opcini.items() if v > 0]),
    }


def dry_run(ukupno: int) -> None:
    opcine = aktivne_opcine_iz_mastera()
    nazivi = [n for n, _, _ in opcine]
    kvote = izracunaj_kvote(nazivi, ukupno)
    log.info("Planirano %s općina. Top 25 kvota:", len(opcine))
    top = sorted(kvote.items(), key=lambda x: -x[1])[:25]
    suma = sum(kvote.values())
    for n, k in top:
        zup = next((z for nn, z, _ in opcine if nn == n), "?")
        ndc = NDC_PO_ZUPANIJI.get(zup, "?")
        log.info("  %-22s NDC=%s  kvota=%s", n, ndc, k)
    log.info("Suma kvota: %s (cilj %s)", suma, ukupno)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ukupno", type=int, default=150_000)
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
        rez = generiraj(db, args.ukupno)
        log.info(
            "Generirano: ukupno=%s, općina=%s. Top 15:",
            rez["ukupno_generirano"],
            rez["broj_opcina"],
        )
        top = sorted(rez["po_opcini"].items(), key=lambda x: -x[1])[:15]
        for n, k in top:
            log.info("  %-22s %s", n, k)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
