"""Import HT Mostar RAK blokova iz Excel datoteke u ht_eronet."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

EXCEL_PATH = Path(r"C:\Telekom_HT\Dodijeljeni blokovi brojeva_h 18-2-2026.xlsx")
DB_URL = "postgresql://postgres:admin@localhost:5432/ht_eronet"

# Plan numeriranja BiH (OHR / ITU) – NDC -> (općina, oznaka županije, entitet)
NDC_OPCINA: dict[str, tuple[str, str, str]] = {
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
    "49": ("Brčko", "KS", "FBiH"),
    "51": ("Banja Luka", "SBŽ", "RS"),
    "63": ("Mostar", "HNŽ", "FBiH"),
    "64": ("Mostar", "HNŽ", "FBiH"),
}


def _digits(value) -> str | None:
    if pd.isna(value):
        return None
    m = re.search(r"\d+", str(value).strip())
    return m.group(0) if m else None


def load_ht_rows() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, sheet_name=0, header=6)
    df.columns = ["NDC", "Blok", "Duzina", "_x", "Operator", "Dodatno"]
    df["NDC"] = df["NDC"].apply(_digits).ffill()
    df["Blok"] = df["Blok"].apply(_digits)
    df["Duzina"] = pd.to_numeric(df["Duzina"], errors="coerce")
    mask = df["Operator"].astype(str).str.contains(
        r"HT d\.d\. Mostar|HT d\.o\.o\. Mostar", case=False, na=False
    )
    rows = df.loc[mask, ["NDC", "Blok", "Duzina"]].dropna()
    return rows.astype({"NDC": str, "Blok": str, "Duzina": int})


def raspon_granice(ndc: str, blok: str, duzina: int) -> tuple[str, str]:
    if duzina == 8:
        return f"{ndc}{blok}00", f"{ndc}{blok}99"
    if duzina == 9:
        return f"{ndc}{blok}000", f"{ndc}{blok}999"
    raise ValueError(f"Nepodržana dužina: {duzina}")


def iter_brojevi(pocetak: str, kraj: str):
    start, end = int(pocetak), int(kraj)
    width = len(pocetak)
    for n in range(start, end + 1):
        yield str(n).zfill(width)


def get_or_create_opcina(cur, naziv: str, oznaka: str, entitet: str) -> int:
    cur.execute("SELECT id FROM opcine WHERE naziv = %s AND entitet = %s", (naziv, entitet))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("SELECT id FROM zupanije WHERE oznaka = %s", (oznaka,))
    z = cur.fetchone()
    if not z:
        raise RuntimeError(f"Županija s oznakom {oznaka} ne postoji")
    cur.execute(
        """
        INSERT INTO opcine (naziv, zupanija_id, entitet)
        VALUES (%s, %s, %s)
        ON CONFLICT (naziv, zupanija_id) DO UPDATE SET entitet = EXCLUDED.entitet
        RETURNING id
        """,
        (naziv, z[0], entitet),
    )
    return cur.fetchone()[0]


def get_or_create_lokacija(cur, opcina_id: int, naziv: str) -> int:
    cur.execute(
        "SELECT id FROM lokacije WHERE opcina_id = %s AND naziv = %s",
        (opcina_id, naziv),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO lokacije (opcina_id, naziv, tip)
        VALUES (%s, %s, 'prodajno_mjesto')
        RETURNING id
        """,
        (opcina_id, naziv),
    )
    return cur.fetchone()[0]


def get_or_create_uredjaj(cur, lokacija_id: int, oznaka: str) -> int:
    cur.execute(
        "SELECT id FROM uredjaji WHERE lokacija_id = %s AND oznaka = %s",
        (lokacija_id, oznaka),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO uredjaji (lokacija_id, tip, oznaka)
        VALUES (%s, 'MSAN', %s)
        RETURNING id
        """,
        (lokacija_id, oznaka),
    )
    return cur.fetchone()[0]


def get_or_create_raspon(cur, uredjaj_id: int, pocetak: str, kraj: str) -> int:
    cur.execute(
        """
        SELECT id FROM rasponi
        WHERE uredjaj_id = %s AND pocetak = %s AND kraj = %s
        """,
        (uredjaj_id, pocetak, kraj),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO rasponi (uredjaj_id, pocetak, kraj)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (uredjaj_id, pocetak, kraj),
    )
    return cur.fetchone()[0]


def main() -> int:
    rows = load_ht_rows()
    if rows.empty:
        print("Nema HT redova za import.", file=sys.stderr)
        return 1

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    added_msisdn = 0
    processed = 0

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM kvaliteta WHERE naziv = 'silver'")
            silver_id = cur.fetchone()[0]

            for _, r in rows.iterrows():
                ndc, blok, duzina = r["NDC"], r["Blok"], int(r["Duzina"])
                if ndc not in NDC_OPCINA:
                    raise RuntimeError(f"NDC {ndc} nije u mapiranju Plan-a numeriranja")

                opcina_naziv, zup_oznaka, entitet = NDC_OPCINA[ndc]
                pocetak, kraj = raspon_granice(ndc, blok, duzina)

                opcina_id = get_or_create_opcina(cur, opcina_naziv, zup_oznaka, entitet)
                lokacija_naziv = f"HT Eronet - {opcina_naziv}"
                lokacija_id = get_or_create_lokacija(cur, opcina_id, lokacija_naziv)
                uredjaj_oznaka = f"MSAN-{ndc}-{blok}"
                uredjaj_id = get_or_create_uredjaj(cur, lokacija_id, uredjaj_oznaka)
                raspon_id = get_or_create_raspon(cur, uredjaj_id, pocetak, kraj)

                brojevi = list(iter_brojevi(pocetak, kraj))
                execute_values(
                    cur,
                    """
                    INSERT INTO msisdn (broj, status, raspon_id, kvaliteta_id)
                    VALUES %s
                    ON CONFLICT (broj) DO NOTHING
                    """,
                    [(b, "slobodan", raspon_id, silver_id) for b in brojevi],
                    template="(%s, %s, %s, %s)",
                )
                added_msisdn += cur.rowcount
                processed += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"Obradeno blokova: {processed}")
    print(f"Novi MSISDN redovi (ON CONFLICT preskočeni): {added_msisdn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
