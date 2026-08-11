"""
Import poštanskih ureda iz popis_ureda.pdf (ili CSV).

Pravilo hijerarhije: grad i općina su sibling jedinice pod županijom/regijom —
ne stavljati općine pod gradove.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.orm import Session

ROW_RE = re.compile(r"^(\d{5})\s+(.+?)\s+(HP|BHP|PS)\s*$", re.MULTILINE)

# Pretpostavljeni entitet po operateru
OPERATER_ENTITET = {"HP": "FBiH", "BHP": "FBiH", "PS": "RS"}

# Heuristika PB (prve 2 znamenke) → oznaka županije/regije kad nema u masteru
PB_ZUPANIJA_FBIH: dict[str, str] = {
    "88": "HNŽ",
    "80": "HBŽ",
    "81": "HNŽ",
    "71": "KS",
    "75": "TK",
    "72": "ZDŽ",
    "70": "SBŽ",
    "77": "USŽ",
    "73": "BPŽ",
    "74": "ZDŽ",
    "76": "ŽP",
    "79": "USŽ",
}

PB_ZUPANIJA_RS: dict[str, str] = {
    "78": "RS-BL",
    "79": "RS-PRI",
    "89": "RS-TRE",
    "74": "RS-DOB",
    "73": "RS-FOC",
    "75": "RS-ZV",
    "76": "RS-BIJ",
    "77": "RS-BL",
    "72": "RS-ISA",
    "71": "RS-ISA",
    "70": "RS-DOB",
}

GRADOVI = {
    "Mostar",
    "Stolac",
    "Sarajevo",
    "Tuzla",
    "Zenica",
    "Livno",
    "Bihać",
    "Goražde",
    "Brčko",
    "Banja Luka",
    "Bijeljina",
    "Doboj",
    "Prijedor",
    "Trebinje",
    "Istočno Sarajevo",
}

BRCKO_PB_PREFIXES = ("760", "761")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_csv_map(path: Path, key_col: str) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    out: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get(key_col) or "").strip()
            if key:
                out[key] = {k: (v or "").strip() for k, v in row.items()}
    return out


def _parse_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _parse_rows_from_text(text: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for m in ROW_RE.finditer(text):
        pb, naziv, op = m.group(1), m.group(2).strip(), m.group(3)
        if naziv and not naziv[0].isalpha() and len(naziv) > 1:
            continue
        rows.append((pb, naziv, op))
    return rows


def _parse_csv(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pb = (row.get("postanski_broj") or row.get("pb") or "").strip()
            naziv = (row.get("naziv_mjesta") or row.get("naziv") or "").strip()
            op = (row.get("operater") or row.get("posta_operater") or "").strip().upper()
            if pb and naziv and op in ("HP", "BHP", "PS"):
                rows.append((pb, naziv, op))
    return rows


def parse_postanski_uredi(path: Path) -> list[tuple[str, str, str]]:
    if not path.is_file():
        raise HTTPException(status_code=400, detail=f"Datoteka ne postoji: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _parse_csv(path)
    if suffix == ".pdf":
        text = _parse_pdf_text(path)
        rows = _parse_rows_from_text(text)
        if not rows:
            raise HTTPException(status_code=400, detail="Iz PDF-a nije izvučen nijedan poštanski ured.")
        return rows
    raise HTTPException(status_code=400, detail="Podržani formati: .pdf, .csv")


def _is_brcko(pb: str, naziv: str) -> bool:
    n = naziv.lower()
    if "brčko" in n or "brcko" in n:
        return True
    return pb.startswith(BRCKO_PB_PREFIXES)


def _entitet_za_red(pb: str, naziv: str, operater: str) -> str:
    if _is_brcko(pb, naziv):
        return "Brčko"
    return OPERATER_ENTITET.get(operater, "FBiH")


def _zupanija_oznaka_heuristika(pb: str, entitet: str) -> str:
    if entitet == "Brčko":
        return "BRC"
    prefix = pb[:2]
    if entitet == "RS":
        return PB_ZUPANIJA_RS.get(prefix, "RS-BL")
    return PB_ZUPANIJA_FBIH.get(prefix, "KS")


def _resolve_opcina(
    naziv_mjesta: str,
    master: dict[str, dict[str, str]],
    overrides: dict[str, dict[str, str]],
    pb: str,
    entitet: str,
) -> tuple[str, str, str | None, bool]:
    """
    Vraća (opcina_naziv, zupanija_oznaka, tip_jedinice, needs_review).
    """
    if naziv_mjesta in overrides:
        o = overrides[naziv_mjesta]
        return (
            o.get("opcina_naziv") or naziv_mjesta,
            o.get("zupanija_oznaka") or _zupanija_oznaka_heuristika(pb, entitet),
            None,
            False,
        )
    if naziv_mjesta in master:
        m = master[naziv_mjesta]
        tip = m.get("tip_jedinice") or None
        if tip == "":
            tip = None
        return (
            m.get("opcina_naziv") or naziv_mjesta,
            m.get("zupanija_oznaka") or _zupanija_oznaka_heuristika(pb, entitet),
            tip,
            False,
        )
    for m in master.values():
        if m.get("opcina_naziv") == naziv_mjesta:
            tip = m.get("tip_jedinice") or None
            return (
                naziv_mjesta,
                m.get("zupanija_oznaka") or _zupanija_oznaka_heuristika(pb, entitet),
                tip,
                False,
            )
    tip = "grad" if naziv_mjesta in GRADOVI else None
    if tip is None and naziv_mjesta.endswith("grad"):
        tip = "opcina"
    zup = _zupanija_oznaka_heuristika(pb, entitet)
    return naziv_mjesta, zup, tip, True


def _get_zupanija_id(db: Session, oznaka: str, entitet: str) -> int:
    row = db.execute(
        text("SELECT id FROM zupanije WHERE oznaka = :o AND entitet = :e LIMIT 1"),
        {"o": oznaka, "e": entitet},
    ).fetchone()
    if row:
        return int(row[0])
    row = db.execute(
        text("SELECT id FROM zupanije WHERE oznaka = :o LIMIT 1"),
        {"o": oznaka},
    ).fetchone()
    if row:
        return int(row[0])
    if entitet == "Brčko":
        row = db.execute(text("SELECT id FROM zupanije WHERE oznaka = 'BRC' LIMIT 1")).fetchone()
        if row:
            return int(row[0])
    fallback = db.execute(
        text("SELECT id FROM zupanije WHERE entitet = :e ORDER BY id LIMIT 1"),
        {"e": entitet},
    ).scalar()
    if not fallback:
        raise HTTPException(status_code=400, detail=f"Nema županije/regije za entitet {entitet}.")
    return int(fallback)


def _get_or_create_opcina(
    db: Session,
    naziv: str,
    zupanija_oznaka: str,
    entitet: str,
    tip_jedinice: str | None,
) -> int:
    zupanija_id = _get_zupanija_id(db, zupanija_oznaka, entitet)
    row = db.execute(
        text("SELECT id FROM opcine WHERE naziv = :n AND zupanija_id = :z LIMIT 1"),
        {"n": naziv, "z": zupanija_id},
    ).fetchone()
    if row:
        if tip_jedinice:
            db.execute(
                text(
                    "UPDATE opcine SET tip_jedinice = COALESCE(tip_jedinice, :t), entitet = :e WHERE id = :id"
                ),
                {"t": tip_jedinice, "e": entitet, "id": row[0]},
            )
        return int(row[0])
    new_id = db.execute(
        text(
            """
            INSERT INTO opcine (naziv, zupanija_id, entitet, tip_jedinice)
            VALUES (:n, :z, :e, :t)
            ON CONFLICT (naziv, zupanija_id) DO UPDATE SET
              entitet = EXCLUDED.entitet,
              tip_jedinice = COALESCE(opcine.tip_jedinice, EXCLUDED.tip_jedinice)
            RETURNING id
            """
        ),
        {"n": naziv, "z": zupanija_id, "e": entitet, "t": tip_jedinice},
    ).scalar_one()
    return int(new_id)


def _upsert_postanski_ured(
    db: Session,
    opcina_id: int,
    naziv_mjesta: str,
    pb: str,
    operater: str,
) -> str:
    """Vraća 'novi' | 'azuriran'."""
    naziv_lok = f"Poštanski ured {naziv_mjesta}"
    row = db.execute(
        text("SELECT id, naziv FROM lokacije WHERE postanski_broj = :pb LIMIT 1"),
        {"pb": pb},
    ).fetchone()
    if row:
        db.execute(
            text(
                """
                UPDATE lokacije SET
                  opcina_id = :o,
                  naziv = :n,
                  tip = 'postanski_ured',
                  posta_operater = :op,
                  updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"o": opcina_id, "n": naziv_lok, "op": operater, "id": row[0]},
        )
        return "azurirani"
    db.execute(
        text(
            """
            INSERT INTO lokacije (opcina_id, naziv, tip, postanski_broj, posta_operater)
            VALUES (:o, :n, 'postanski_ured', :pb, :op)
            """
        ),
        {"o": opcina_id, "n": naziv_lok, "pb": pb, "op": operater},
    )
    return "novi"


def import_postanski_uredi(
    db: Session,
    path: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root()
    if path is None:
        path = root / "popis_ureda.pdf"
    if not path.is_file():
        alt = root / "data" / "postanski_uredi.csv"
        path = alt if alt.is_file() else path

    master_path = root / "data" / "opcine_master.csv"
    override_path = root / "data" / "postanski_opcina_map.csv"
    master = _load_csv_map(master_path, "naziv_mjesta")
    overrides = _load_csv_map(override_path, "naziv_mjesta")

    rows = parse_postanski_uredi(path)
    stats: dict[str, Any] = {
        "ukupno": len(rows),
        "novi": 0,
        "azurirani": 0,
        "preskoceni": 0,
        "needs_review": [],
        "po_operateru": {"HP": 0, "BHP": 0, "PS": 0},
    }

    for pb, naziv_mjesta, operater in rows:
        stats["po_operateru"][operater] = stats["po_operateru"].get(operater, 0) + 1
        entitet = _entitet_za_red(pb, naziv_mjesta, operater)
        opcina_naziv, zup_oznaka, tip, needs_review = _resolve_opcina(
            naziv_mjesta, master, overrides, pb, entitet
        )
        if entitet == "Brčko":
            zup_oznaka = "BRC"
        try:
            opcina_id = _get_or_create_opcina(db, opcina_naziv, zup_oznaka, entitet, tip)
            action = _upsert_postanski_ured(db, opcina_id, naziv_mjesta, pb, operater)
            stats[action] = stats.get(action, 0) + 1
            if needs_review:
                stats["needs_review"].append(
                    {"pb": pb, "naziv": naziv_mjesta, "operater": operater, "opcina": opcina_naziv}
                )
        except Exception as exc:
            stats["preskoceni"] += 1
            stats["needs_review"].append(
                {"pb": pb, "naziv": naziv_mjesta, "greska": str(exc)}
            )

    db.commit()
    stats["needs_review_count"] = len(stats["needs_review"])
    return stats
