"""Geografska raspodjela MSISDN-a iz RAK Excela na općine po županiji.

Cilj: brojevi iz jednog NDC bloka ne smiju završiti samo na čvornoj općini
(npr. Mostar za NDC 36/63/64), nego se ravnomjerno raspodijele na sve općine
unutar pripadajuće županije iz `data/opcine_master.csv`. Korisnici iz Čapljine,
Stolca, Neuma itd. moraju moći dobiti broj iz HNŽ poola.

Pravila prioriteta:
1. `rak_ndc_opcina_map.csv` – ručna iznimka po NDC+Blok.
2. `NDC_OPCINA` čvor + raspodjela na sve općine njegove županije.
3. Banja Luka (NDC 51) i Brčko (NDC 49) idu cijeli na svoju jednu općinu (bez
   širenja na RS regiju ili Distrikt).
"""
from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

NDC_OPCINA_FALLBACK: dict[str, tuple[str, str, str]] = {
    "30": ("Travnik", "SBŽ", "FBiH"),
    "31": ("Orašje", "ŽP", "FBiH"),
    "32": ("Zenica", "ZDŽ", "FBiH"),
    "33": ("Sarajevo", "KS", "FBiH"),
    "34": ("Livno", "HBŽ", "FBiH"),
    "35": ("Tuzla", "TK", "FBiH"),
    "36": ("Mostar", "HNŽ", "FBiH"),
    "37": ("Bihać", "USŽ", "FBiH"),
    "38": ("Goražde", "BPŽ", "FBiH"),
    "39": ("Široki Brijeg", "ZHŽ", "FBiH"),
    "49": ("Brčko", "BRC", "Brčko"),
    "51": ("Banja Luka", "RS-BL", "RS"),
    "63": ("Mostar", "HNŽ", "FBiH"),
    "64": ("Mostar", "HNŽ", "FBiH"),
}

NDC_BEZ_RASPODJELE: set[str] = {"49", "51"}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPCINE_MASTER = PROJECT_ROOT / "data" / "opcine_master.csv"
NDC_MAP_CSV = PROJECT_ROOT / "data" / "rak_ndc_opcina_map.csv"


@dataclass(frozen=True)
class OpcinaGeo:
    naziv: str
    zupanija_oznaka: str
    entitet: str


def _normaliziraj(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def ucitaj_opcine_master() -> list[OpcinaGeo]:
    if not OPCINE_MASTER.exists():
        logger.warning("opcine_master.csv ne postoji: %s", OPCINE_MASTER)
        return []
    out: list[OpcinaGeo] = []
    with OPCINE_MASTER.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            opc = _normaliziraj(row.get("opcina_naziv") or row.get("naziv_mjesta") or "")
            zup = _normaliziraj(row.get("zupanija_oznaka") or "")
            ent = _normaliziraj(row.get("entitet") or "")
            if not (opc and zup and ent):
                continue
            out.append(OpcinaGeo(opc, zup, ent))
    seen: set[tuple[str, str]] = set()
    dedup: list[OpcinaGeo] = []
    for o in out:
        key = (o.naziv, o.zupanija_oznaka)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(o)
    return dedup


def ucitaj_ndc_blok_iznimke() -> dict[tuple[str, str], OpcinaGeo]:
    """`data/rak_ndc_opcina_map.csv` (opcionalno) – ručna iznimka po NDC[+Blok]."""
    if not NDC_MAP_CSV.exists():
        return {}
    iznimke: dict[tuple[str, str], OpcinaGeo] = {}
    with NDC_MAP_CSV.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ndc = _normaliziraj(row.get("ndc") or "")
            blok = _normaliziraj(row.get("blok") or "")
            opc = _normaliziraj(row.get("opcina_naziv") or "")
            zup = _normaliziraj(row.get("zupanija_oznaka") or "")
            ent = _normaliziraj(row.get("entitet") or "")
            if not (ndc and opc and zup and ent):
                continue
            iznimke[(ndc, blok)] = OpcinaGeo(opc, zup, ent)
    return iznimke


def opcine_za_zupaniju(master: list[OpcinaGeo], zupanija_oznaka: str) -> list[OpcinaGeo]:
    return [o for o in master if o.zupanija_oznaka == zupanija_oznaka]


def odredi_primarnu_opcinu(
    ndc: str,
    blok: str,
    excel_opcina: str | None,
    iznimke: dict[tuple[str, str], OpcinaGeo],
    master: list[OpcinaGeo],
) -> OpcinaGeo:
    if (ndc, blok) in iznimke:
        return iznimke[(ndc, blok)]
    if (ndc, "") in iznimke:
        return iznimke[(ndc, "")]

    if excel_opcina:
        naziv = _normaliziraj(excel_opcina)
        for o in master:
            if o.naziv.lower() == naziv.lower():
                return o

    fb = NDC_OPCINA_FALLBACK.get(ndc)
    if fb:
        return OpcinaGeo(fb[0], fb[1], fb[2])

    raise ValueError(f"Ne mogu odrediti općinu za NDC {ndc} Blok {blok}.")


def odredi_listu_opcina(
    ndc: str,
    primarna: OpcinaGeo,
    master: list[OpcinaGeo],
) -> list[OpcinaGeo]:
    """Lista općina koje dobivaju dio brojeva iz ovog RAK reda.

    - NDC 49 (Brčko) i 51 (Banja Luka) idu cijeli na jednu općinu.
    - Inače: sve općine županije iz `opcine_master`. Primarna ide prva
      (round-robin start), pa abecedno ostatak.
    """
    if ndc in NDC_BEZ_RASPODJELE:
        return [primarna]

    zup_opcine = opcine_za_zupaniju(master, primarna.zupanija_oznaka)
    if not zup_opcine:
        return [primarna]

    ostale = [o for o in zup_opcine if o.naziv != primarna.naziv]
    ostale.sort(key=lambda o: o.naziv.lower())
    if any(o.naziv == primarna.naziv for o in zup_opcine):
        return [primarna] + ostale
    return [primarna] + ostale


def slug_opcina(naziv: str) -> str:
    repl = {
        "č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj",
        "Č": "C", "Ć": "C", "Š": "S", "Ž": "Z", "Đ": "Dj",
    }
    s = naziv
    for k, v in repl.items():
        s = s.replace(k, v)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s.upper()


def osiguraj_zupaniju(db: Session, oznaka: str, entitet: str) -> int:
    row = db.execute(text("SELECT id FROM zupanije WHERE oznaka = :o"), {"o": oznaka}).fetchone()
    if row:
        return int(row[0])
    naziv = f"Regija {oznaka}" if entitet == "RS" else oznaka
    sjediste = oznaka
    new_id = db.execute(
        text(
            """
            INSERT INTO zupanije (oznaka, naziv, entitet, sjediste)
            VALUES (:o, :n, :e, :s)
            RETURNING id
            """
        ),
        {"o": oznaka, "n": naziv, "e": entitet, "s": sjediste},
    ).scalar_one()
    return int(new_id)


def osiguraj_opcinu(db: Session, naziv: str, zupanija_oznaka: str, entitet: str) -> int:
    """Vrati ID općine za (naziv, zupanija_oznaka).

    Logika:
    1. Ako postoji točno (naziv, zupanija_id) → vrati ga.
    2. Ako postoji općina s istim nazivom u drugoj županiji – premjesti je u
       traženu (osim ako se time gubi povijesni inventar; preferiraj UPDATE).
    3. Inače kreiraj novu.
    """
    zid = osiguraj_zupaniju(db, zupanija_oznaka, entitet)

    row = db.execute(
        text("SELECT id, zupanija_id, entitet FROM opcine WHERE naziv = :n AND zupanija_id = :z"),
        {"n": naziv, "z": zid},
    ).fetchone()
    if row:
        if row[2] != entitet:
            db.execute(
                text("UPDATE opcine SET entitet = :e WHERE id = :id"),
                {"e": entitet, "id": int(row[0])},
            )
        return int(row[0])

    row_any = db.execute(
        text("SELECT id, zupanija_id, entitet FROM opcine WHERE naziv = :n ORDER BY id"),
        {"n": naziv},
    ).fetchall()
    if row_any:
        opc_id = int(row_any[0][0])
        db.execute(
            text("UPDATE opcine SET zupanija_id = :z, entitet = :e WHERE id = :id"),
            {"z": zid, "e": entitet, "id": opc_id},
        )
        for extra in row_any[1:]:
            extra_id = int(extra[0])
            db.execute(
                text("UPDATE lokacije SET opcina_id = :main WHERE opcina_id = :extra"),
                {"main": opc_id, "extra": extra_id},
            )
            db.execute(text("DELETE FROM opcine WHERE id = :id"), {"id": extra_id})
        return opc_id

    new_id = db.execute(
        text(
            """
            INSERT INTO opcine (naziv, zupanija_id, entitet)
            VALUES (:n, :z, :e)
            ON CONFLICT (naziv, zupanija_id) DO UPDATE SET entitet = EXCLUDED.entitet
            RETURNING id
            """
        ),
        {"n": naziv, "z": zid, "e": entitet},
    ).scalar_one()
    return int(new_id)
