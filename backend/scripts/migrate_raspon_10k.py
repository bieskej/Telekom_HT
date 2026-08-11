"""Migracija postojećih RAK raspona na novu formulu (sn_len) + raspodjelu po općini.

Pristup:
1. Pročita sve raspone iz baze: (ndc, blok, duzina, pocetak, kraj).
2. Za svaki raspon izračuna novu (pocetak, kraj) po `raspon_granice` (sn_len).
3. Ako je novi raspon širi (npr. NDC 64 Dužina 9 prefiks 5 → 10 000 brojeva),
   generira sve nove MSISDN-e koji nedostaju.
4. Brojeve raspodjeljuje round-robin na sve općine županije iz `opcine_master.csv`
   (osim NDC 49 → samo Brčko i NDC 51 → samo Banja Luka).
5. Ne briše zauzete/karantena bez `--force`. Stare slobodne brojeve koji više
   ne pripadaju (jer su raspon-i preraspoređeni na druge općine) može
   `--fresh-rak-reimport` ukloniti.

CLI:
    python -m scripts.migrate_raspon_10k --dry-run
    python -m scripts.migrate_raspon_10k --fresh-rak-reimport
    python -m scripts.migrate_raspon_10k --fresh-rak-reimport --force

Sigurnost:
- Bez `--fresh-rak-reimport` skripta SAMO dodaje brojeve koji nedostaju
  (postojeći zauzeti/karantena/slobodni se ne diraju).
- `--fresh-rak-reimport` briše SAMO slobodne (status='slobodan') MSISDN-e,
  rasponi i uređaji ostaju. Karantena/zauzeti ostaju netaknuti.
- `--force` dodatno dopušta brisanje karantena (ne zauzetih).
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.services.kvaliteta_klasifikacija import klasificiraj_broj  # noqa: E402
from app.services.rak_geografija import (  # noqa: E402
    NDC_OPCINA_FALLBACK,
    odredi_listu_opcina,
    odredi_primarnu_opcinu,
    osiguraj_opcinu,
    slug_opcina,
    ucitaj_ndc_blok_iznimke,
    ucitaj_opcine_master,
)
from app.services.rak_import import (  # noqa: E402
    _get_or_create_lokacija,
    _get_or_create_raspon,
    _get_or_create_uredjaj,
    iter_brojevi,
    raspon_granice,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("migrate_raspon_10k")


def parsiraj_raspon_oznaku(oznaka: str) -> tuple[str, str] | None:
    """`MSAN-30-3049-...` ili `MSAN-30-3049` → (ndc, blok)."""
    if not oznaka.startswith("MSAN-"):
        return None
    djelovi = oznaka.split("-")
    if len(djelovi) < 3:
        return None
    ndc, blok = djelovi[1], djelovi[2]
    if not ndc.isdigit() or not blok.isdigit():
        return None
    return ndc, blok


def izvuci_rak_redove(db) -> list[dict]:
    """Iz baze izvuče jedinstvene (ndc, blok, duzina) raspona za reimport."""
    rows = db.execute(
        text(
            """
            SELECT DISTINCT u.oznaka, r.pocetak, r.kraj, length(r.pocetak) AS dlz
            FROM rasponi r
            JOIN uredjaji u ON u.id = r.uredjaj_id
            ORDER BY r.pocetak
            """
        )
    ).fetchall()
    redovi: dict[tuple[str, str, int], None] = {}
    for r in rows:
        parsed = parsiraj_raspon_oznaku(r.oznaka)
        if not parsed:
            continue
        ndc, blok = parsed
        duzina = int(r.dlz)
        redovi.setdefault((ndc, blok, duzina), None)
    return [{"ndc": n, "blok": b, "duzina": d} for (n, b, d) in redovi.keys()]


def cisti_slobodne_msisdn(db, force_karantena: bool = False) -> int:
    """Obriši slobodne MSISDN-e (i karantenu ako force). Zauzeti ostaju uvijek."""
    res = db.execute(
        text(
            """
            DELETE FROM msisdn
            WHERE status = 'slobodan'
            """
        )
    )
    obrisano = res.rowcount or 0
    if force_karantena:
        res2 = db.execute(
            text(
                """
                DELETE FROM msisdn
                WHERE status = 'karantena'
                """
            )
        )
        obrisano += res2.rowcount or 0
    log.info("Obrisano slobodnih/karantena MSISDN-a: %s", obrisano)
    return obrisano


def reimport(db, fresh: bool, force: bool) -> dict:
    redovi = izvuci_rak_redove(db)
    log.info("Pronađeno %s jedinstvenih RAK redova iz postojećih raspona.", len(redovi))

    inventura: dict[tuple[str, str, int], dict] = {}
    for r in redovi:
        ndc, blok, duzina = r["ndc"], r["blok"], r["duzina"]
        try:
            pocetak, kraj = raspon_granice(ndc, blok, duzina)
        except ValueError as exc:
            log.warning("Preskačem (ndc=%s blok=%s duzina=%s): %s", ndc, blok, duzina, exc)
            continue
        inventura[(ndc, blok, duzina)] = {
            "pocetak": pocetak,
            "kraj": kraj,
            "brojeva": 10 ** (duzina - len(f"{ndc}{blok}")),
        }

    ukupno_plan = sum(v["brojeva"] for v in inventura.values())
    log.info("Plan: %s redova, %s brojeva po novoj formuli.", len(inventura), ukupno_plan)

    if fresh:
        cisti_slobodne_msisdn(db, force_karantena=force)

    master = ucitaj_opcine_master()
    iznimke = ucitaj_ndc_blok_iznimke()

    kvaliteta_ids = {
        row[0]: row[1]
        for row in db.execute(text("SELECT naziv, id FROM kvaliteta")).fetchall()
    }
    novi_brojevi = 0
    preskoceni = 0
    raspodjela: dict[str, int] = defaultdict(int)

    for (ndc, blok, duzina), info in inventura.items():
        pocetak, kraj = info["pocetak"], info["kraj"]
        try:
            primarna = odredi_primarnu_opcinu(ndc, blok, None, iznimke, master)
        except ValueError as exc:
            log.warning("Preskačem NDC=%s Blok=%s (geografija): %s", ndc, blok, exc)
            continue
        lista_opc = odredi_listu_opcina(ndc, primarna, master)

        raspon_id_po_opcini: dict[str, int] = {}
        for op in lista_opc:
            opcina_id = osiguraj_opcinu(db, op.naziv, op.zupanija_oznaka, op.entitet)
            lok_id = _get_or_create_lokacija(db, opcina_id, f"HT Eronet - {op.naziv}")
            ured_id = _get_or_create_uredjaj(
                db, lok_id, f"MSAN-{ndc}-{blok}-{slug_opcina(op.naziv)}"
            )
            raspon_id, _ = _get_or_create_raspon(db, ured_id, pocetak, kraj)
            raspon_id_po_opcini[op.naziv] = raspon_id

        for idx, broj in enumerate(iter_brojevi(pocetak, kraj)):
            op = lista_opc[idx % len(lista_opc)]
            inserted = db.execute(
                text(
                    """
                    INSERT INTO msisdn (broj, status, raspon_id, kvaliteta_id)
                    VALUES (:broj, 'slobodan', :raspon_id, :kvaliteta_id)
                    ON CONFLICT (broj) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "broj": broj,
                    "raspon_id": raspon_id_po_opcini[op.naziv],
                    "kvaliteta_id": kvaliteta_ids[klasificiraj_broj(broj)],
                },
            ).fetchone()
            if inserted:
                novi_brojevi += 1
                raspodjela[op.naziv] += 1
            else:
                preskoceni += 1

    db.commit()
    return {"novi_brojevi": novi_brojevi, "preskoceni": preskoceni, "raspodjela": dict(raspodjela)}


def dry_run(db) -> dict:
    redovi = izvuci_rak_redove(db)
    plan_rows = []
    ukupno = 0
    master = ucitaj_opcine_master()
    iznimke = ucitaj_ndc_blok_iznimke()
    po_opcini: dict[str, int] = defaultdict(int)
    for r in redovi:
        ndc, blok, duzina = r["ndc"], r["blok"], r["duzina"]
        try:
            pocetak, kraj = raspon_granice(ndc, blok, duzina)
        except ValueError as exc:
            plan_rows.append({**r, "status": f"preskočen: {exc}"})
            continue
        broj = 10 ** (duzina - len(f"{ndc}{blok}"))
        ukupno += broj
        try:
            primarna = odredi_primarnu_opcinu(ndc, blok, None, iznimke, master)
            lista = odredi_listu_opcina(ndc, primarna, master)
            for idx in range(broj):
                op = lista[idx % len(lista)]
                po_opcini[op.naziv] += 1
        except ValueError:
            pass
        plan_rows.append(
            {**r, "pocetak": pocetak, "kraj": kraj, "brojeva": broj, "status": "OK"}
        )
    return {"redovi": plan_rows, "ukupno": ukupno, "po_opcini": dict(po_opcini)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Samo izračun, bez izmjene baze.")
    parser.add_argument(
        "--fresh-rak-reimport",
        action="store_true",
        help="Briši slobodne MSISDN-e prije reimporta (zauzeti ostaju).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Dopusti brisanje karantena MSISDN-a. Zauzeti se NIKAD ne brišu.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.dry_run:
            plan = dry_run(db)
            log.info("Ukupno brojeva u planu: %s", plan["ukupno"])
            log.info("Po općini (top 20):")
            top = sorted(plan["po_opcini"].items(), key=lambda x: -x[1])[:20]
            for op, n in top:
                log.info("  %-25s %s", op, n)
            return 0

        if args.fresh_rak_reimport:
            log.warning("Pokrenut --fresh-rak-reimport. force=%s.", args.force)

        res = reimport(db, fresh=args.fresh_rak_reimport, force=args.force)
        log.info("Novih brojeva: %s, preskočenih (već postoje): %s", res["novi_brojevi"], res["preskoceni"])
        log.info("Raspodjela po općini (top 20):")
        top = sorted(res["raspodjela"].items(), key=lambda x: -x[1])[:20]
        for op, n in top:
            log.info("  %-25s %s", op, n)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
