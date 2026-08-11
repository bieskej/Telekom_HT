"""Import HT Eronet RAK blokova iz Excel/CSV datoteke.

Generator brojeva slijedi RAK Plan numeriranja BiH (E.164, max 9 znamenki za N(S)N).

Formula (po prompt-u korisnika, 2026):
    prefiks  = NDC + Blok   (samo znamenke)
    sn_len   = Duzina - len(prefiks)
    Duzina   = ukupna duljina N(S)N (8 ili 9 u praksi, max 9 po E.164)
    brojeva  = 10 ** sn_len     (sve kombinacije serijskog sufiksa)

Kad je sn_len == 4 (Duzina 9, prefiks 5 znamenki, npr. NDC 64 + Blok 3-znamenki):
jedan RAK red daje **10 000** brojeva.

Geografska raspodjela: brojevi se ravnomjerno (round-robin) raspoređuju na sve
općine županije koja pripada primarnoj općini NDC-a (vidi `rak_geografija`).
HNŽ pool: Mostar, Stolac, Čapljina, Čitluk, Crnići, Hodovo, Ravno, Neum, Prozor,
Jablanica, Konjic. Banja Luka (NDC 51) i Brčko (NDC 49) ostaju cijeli na jednoj
općini.
"""
from __future__ import annotations

import io
import logging
import re
from typing import BinaryIO, Iterator

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.kvaliteta_klasifikacija import klasificiraj_broj
from app.services.rak_geografija import (
    NDC_OPCINA_FALLBACK,
    OpcinaGeo,
    odredi_listu_opcina,
    odredi_primarnu_opcinu,
    osiguraj_opcinu,
    slug_opcina,
    ucitaj_ndc_blok_iznimke,
    ucitaj_opcine_master,
)

logger = logging.getLogger(__name__)

NDC_OPCINA: dict[str, tuple[str, str, str]] = dict(NDC_OPCINA_FALLBACK)

HT_OPERATOR_PATTERN = re.compile(r"HT d\.d\. Mostar|HT d\.o\.o\. Mostar", re.I)


def _digits(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    m = re.search(r"\d+", str(value).strip())
    return m.group(0) if m else None


def _ucitaj_dataframe(file: BinaryIO, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()
    if name.endswith(".csv"):
        raw = file.read()
        for encoding in ("utf-8-sig", "utf-8", "cp1250", "latin-1"):
            try:
                return pd.read_csv(io.BytesIO(raw), header=6, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise HTTPException(status_code=400, detail="CSV datoteka nije u podržanom encodingu.")
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file, sheet_name=0, header=6)
    raise HTTPException(status_code=400, detail="Dozvoljeni formati: .xlsx, .csv")


def _normaliziraj_stupce(df: pd.DataFrame) -> pd.DataFrame:
    cols = {str(c).strip().lower(): c for c in df.columns}
    ndc_col = next((cols[k] for k in cols if "ndc" in k), df.columns[0] if len(df.columns) else None)
    blok_col = next((cols[k] for k in cols if "blok" in k), df.columns[1] if len(df.columns) > 1 else None)
    duz_col = next(
        (cols[k] for k in cols if "duz" in k or "duž" in k or "length" in k),
        df.columns[2] if len(df.columns) > 2 else None,
    )
    op_col = next((cols[k] for k in cols if "operator" in k or "operater" in k), None)
    if op_col is None:
        for c in df.columns:
            if df[c].astype(str).str.contains("HT", case=False, na=False).any():
                op_col = c
                break
    opc_col = next((cols[k] for k in cols if "opci" in k or "općin" in k or "opcin" in k), None)

    if not all([ndc_col, blok_col, duz_col, op_col]):
        raise HTTPException(
            status_code=400,
            detail="Datoteka mora sadržavati stupce NDC, Blok, Dužina i Operator.",
        )
    use_cols = [ndc_col, blok_col, duz_col, op_col]
    rename = ["NDC", "Blok", "Duzina", "Operator"]
    if opc_col is not None and opc_col not in use_cols:
        use_cols.append(opc_col)
        rename.append("Opcina")
    out = df[use_cols].copy()
    out.columns = rename
    if "Opcina" not in out.columns:
        out["Opcina"] = None
    return out


def _filtriraj_ht_redove(df: pd.DataFrame) -> pd.DataFrame:
    df["NDC"] = df["NDC"].apply(_digits).ffill()
    df["Blok"] = df["Blok"].apply(_digits)
    df["Duzina"] = pd.to_numeric(df["Duzina"], errors="coerce")
    mask = df["Operator"].astype(str).str.contains(HT_OPERATOR_PATTERN, na=False)
    rows = df.loc[mask, ["NDC", "Blok", "Duzina", "Opcina"]].dropna(subset=["NDC", "Blok", "Duzina"])
    rows = rows.copy()
    rows["NDC"] = rows["NDC"].astype(str)
    rows["Blok"] = rows["Blok"].astype(str)
    rows["Duzina"] = rows["Duzina"].astype(int)
    return rows


def raspon_granice(ndc: str, blok: str, duzina: int) -> tuple[str, str]:
    """Granice MSISDN raspona iz jednog RAK reda po formuli sn_len.

    `Duzina` je ukupna duljina N(S)N (E.164 max 9). `prefiks = NDC + Blok`,
    `sn_len = duzina - len(prefiks)`. Ako je sn_len <= 0 funkcija baca ValueError
    (red se mora preskočiti u importu).

    Primjeri:
        raspon_granice("30","3049",8)  -> ("30304900","30304999")   # 100
        raspon_granice("36","3612",9)  -> ("363612000","363612999") # 1000
        raspon_granice("64","440",9)   -> ("644400000","644409999") # 10 000
    """
    prefiks = f"{ndc}{blok}"
    sn_len = int(duzina) - len(prefiks)
    if sn_len <= 0:
        raise ValueError(
            f"Nemoguć raspon: NDC={ndc} Blok={blok} Dužina={duzina} "
            f"daje sn_len={sn_len} (prefiks {len(prefiks)} znamenki)."
        )
    if int(duzina) > 9:
        raise ValueError(f"Dužina {duzina} prelazi E.164 max 9 znamenki.")
    pocetak = f"{prefiks}{'0' * sn_len}"
    kraj = f"{prefiks}{'9' * sn_len}"
    return pocetak, kraj


def iter_brojevi(pocetak: str, kraj: str) -> Iterator[str]:
    start, end = int(pocetak), int(kraj)
    width = len(pocetak)
    for n in range(start, end + 1):
        yield str(n).zfill(width)


def _get_zupanija_id(db: Session, oznaka: str) -> int:
    zid = db.execute(text("SELECT id FROM zupanije WHERE oznaka = :o"), {"o": oznaka}).scalar()
    if zid:
        return int(zid)
    fallback = db.execute(text("SELECT id FROM zupanije ORDER BY id LIMIT 1")).scalar()
    if not fallback:
        raise HTTPException(status_code=400, detail="U bazi nema županija za mapiranje općina.")
    return int(fallback)


def _get_or_create_lokacija(db: Session, opcina_id: int, naziv: str) -> int:
    row = db.execute(
        text("SELECT id FROM lokacije WHERE opcina_id = :o AND naziv = :n"),
        {"o": opcina_id, "n": naziv},
    ).fetchone()
    if row:
        return int(row[0])
    return int(
        db.execute(
            text(
                """
                INSERT INTO lokacije (opcina_id, naziv, tip)
                VALUES (:o, :n, 'prodajno_mjesto')
                RETURNING id
                """
            ),
            {"o": opcina_id, "n": naziv},
        ).scalar_one()
    )


def _get_or_create_uredjaj(db: Session, lokacija_id: int, oznaka: str) -> int:
    row = db.execute(
        text("SELECT id FROM uredjaji WHERE lokacija_id = :l AND oznaka = :o"),
        {"l": lokacija_id, "o": oznaka},
    ).fetchone()
    if row:
        return int(row[0])
    return int(
        db.execute(
            text(
                """
                INSERT INTO uredjaji (lokacija_id, tip, oznaka)
                VALUES (:l, 'MSAN', :o)
                RETURNING id
                """
            ),
            {"l": lokacija_id, "o": oznaka},
        ).scalar_one()
    )


def _get_or_create_raspon(db: Session, uredjaj_id: int, pocetak: str, kraj: str) -> tuple[int, bool]:
    row = db.execute(
        text(
            "SELECT id FROM rasponi WHERE uredjaj_id = :u AND pocetak = :p AND kraj = :k"
        ),
        {"u": uredjaj_id, "p": pocetak, "k": kraj},
    ).fetchone()
    if row:
        return int(row[0]), False
    new_id = db.execute(
        text(
            """
            INSERT INTO rasponi (uredjaj_id, pocetak, kraj)
            VALUES (:u, :p, :k)
            RETURNING id
            """
        ),
        {"u": uredjaj_id, "p": pocetak, "k": kraj},
    ).scalar_one()
    return int(new_id), True


def _osiguraj_raspon_za_opcinu(
    db: Session,
    opcina: OpcinaGeo,
    ndc: str,
    blok: str,
    pocetak: str,
    kraj: str,
) -> tuple[int, bool]:
    opcina_id = osiguraj_opcinu(db, opcina.naziv, opcina.zupanija_oznaka, opcina.entitet)
    lokacija_id = _get_or_create_lokacija(db, opcina_id, f"HT Eronet - {opcina.naziv}")
    uredjaj_id = _get_or_create_uredjaj(
        db,
        lokacija_id,
        f"MSAN-{ndc}-{blok}-{slug_opcina(opcina.naziv)}",
    )
    return _get_or_create_raspon(db, uredjaj_id, pocetak, kraj)


def import_rak_datoteka(file: BinaryIO, filename: str, db: Session) -> dict:
    try:
        df_raw = _ucitaj_dataframe(file, filename)
        df = _normaliziraj_stupce(df_raw)
        rows = _filtriraj_ht_redove(df)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Greška pri čitanju datoteke: {exc}") from exc

    if rows.empty:
        raise HTTPException(status_code=400, detail="Nema HT redova za import u datoteci.")

    master = ucitaj_opcine_master()
    iznimke = ucitaj_ndc_blok_iznimke()

    kvaliteta_ids = {
        row[0]: row[1]
        for row in db.execute(text("SELECT naziv, id FROM kvaliteta")).fetchall()
    }
    novi_rasponi = 0
    novi_brojevi = 0
    preskoceni = 0
    ukupno_pokusano = 0
    preskoceni_redovi: list[str] = []
    raspodjela_log: dict[str, int] = {}

    for _, r in rows.iterrows():
        ndc = str(r["NDC"])
        blok = str(r["Blok"])
        duzina = int(r["Duzina"])
        excel_opcina = r.get("Opcina")
        excel_opcina = str(excel_opcina).strip() if excel_opcina and not pd.isna(excel_opcina) else None

        try:
            pocetak, kraj = raspon_granice(ndc, blok, duzina)
        except ValueError as exc:
            preskoceni_redovi.append(f"NDC={ndc} Blok={blok} D={duzina}: {exc}")
            logger.warning("RAK red preskočen: %s", exc)
            continue

        try:
            primarna = odredi_primarnu_opcinu(ndc, blok, excel_opcina, iznimke, master)
        except ValueError as exc:
            preskoceni_redovi.append(f"NDC={ndc} Blok={blok}: {exc}")
            logger.warning("RAK red preskočen (geo): %s", exc)
            continue

        lista_opcina = odredi_listu_opcina(ndc, primarna, master)
        raspon_id_po_opcini: dict[str, int] = {}
        for op in lista_opcina:
            rid, novi = _osiguraj_raspon_za_opcinu(db, op, ndc, blok, pocetak, kraj)
            raspon_id_po_opcini[op.naziv] = rid
            if novi:
                novi_rasponi += 1

        for idx, broj in enumerate(iter_brojevi(pocetak, kraj)):
            ukupno_pokusano += 1
            opc = lista_opcina[idx % len(lista_opcina)]
            raspon_id = raspon_id_po_opcini[opc.naziv]
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
                    "raspon_id": raspon_id,
                    "kvaliteta_id": kvaliteta_ids[klasificiraj_broj(broj)],
                },
            ).fetchone()
            if inserted:
                novi_brojevi += 1
                raspodjela_log[opc.naziv] = raspodjela_log.get(opc.naziv, 0) + 1
            else:
                preskoceni += 1

    db.commit()
    return {
        "novi_rasponi": novi_rasponi,
        "novi_brojevi": novi_brojevi,
        "preskoceni": preskoceni,
        "obradeno_blokova": len(rows),
        "ukupno_pokusano": ukupno_pokusano,
        "preskoceni_redovi": preskoceni_redovi,
        "raspodjela_po_opcini": raspodjela_log,
    }
