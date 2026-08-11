"""
Demo seed: ciljana zauzetost po općini za dashboard (mapa + grafikoni).

Postavlja ~51% za Goražde i ~91% za Crnići označavanjem demo MSISDN-a kao zauzet.
Dira SAMO te dvije općine. Demo redovi imaju jmbg LIKE '9999%' ili ime='Demo'.

Dashboard formula (statistike.po_opcini):
    postotak = (zauzet + karantena + portano) / ukupno * 100

CLI:
    cd backend
    python -m scripts.seed_demo_iskoristivost           # primijeni
    python -m scripts.seed_demo_iskoristivost --notify  # primijeni + email alert (>=90%)
    python -m scripts.seed_demo_iskoristivost --dry-run
    python -m scripts.seed_demo_iskoristivost --reset  # ukloni samo demo zauzete

Sigurnost:
    - Ne dira zauzete brojeve koji NISU demo (stvarni korisnici).
    - --reset vraća na slobodan samo demo označene redove.
    - Samo za dev/demo bazu — ne pokretati na produkciji.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.services.jmbg import validiraj_jmbg  # noqa: E402

# (naziv općine u bazi, ciljani postotak zauzetosti)
DEMO_CILJEVI: list[tuple[str, float]] = [
    ("Goražde", 51.0),
    ("Crnići", 91.0),
]

OPCINA_JOIN = """
    JOIN rasponi r ON r.id = m.raspon_id
    JOIN uredjaji u ON u.id = r.uredjaj_id
    JOIN lokacije l ON l.id = u.lokacija_id
    JOIN opcine o ON o.id = l.opcina_id
"""

ZAUZET_STATUS = "('zauzet', 'karantena', 'portano')"

DEMO_JMBG_WHERE = "(m.jmbg LIKE '9999%' OR (m.ime = 'Demo' AND m.prezime LIKE 'Korisnik%'))"


def generiraj_demo_jmbg(serijski: int) -> str:
    """JMBG s prefiksom 9999… (modul 11) za prepoznavanje demo redova."""
    ser = str(serijski % 1000).zfill(3)
    baza = f"999900050{ser}"
    weights = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    total = sum(int(baza[i]) * weights[i] for i in range(12))
    remainder = total % 11
    kontrolna = 11 - remainder
    if kontrolna in (10, 11):
        kontrolna = 0
    jmbg = baza + str(kontrolna)
    if not validiraj_jmbg(jmbg) or not jmbg.startswith("9999"):
        raise ValueError(f"Neispravan demo JMBG: {jmbg}")
    return jmbg


def cilj_zauzeto(ukupno: int, postotak: float) -> int:
    """Broj zauzetih MSISDN-a za ciljani postotak (zaokruženo)."""
    if ukupno <= 0:
        return 0
    return round(ukupno * postotak / 100)


def _broj_statistike(db: Session, opcina_naziv: str) -> dict:
    row = db.execute(
        text(
            f"""
            SELECT
                COUNT(m.id)::int AS ukupno,
                COUNT(m.id) FILTER (WHERE m.status IN {ZAUZET_STATUS})::int AS zauzeto,
                COUNT(m.id) FILTER (
                    WHERE m.status IN {ZAUZET_STATUS} AND {DEMO_JMBG_WHERE}
                )::int AS demo_zauzeto,
                COUNT(m.id) FILTER (WHERE m.status = 'slobodan')::int AS slobodno
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE o.naziv = :naziv
            """
        ),
        {"naziv": opcina_naziv},
    ).one()
    return {
        "ukupno": row.ukupno or 0,
        "zauzeto": row.zauzeto or 0,
        "demo_zauzeto": row.demo_zauzeto or 0,
        "slobodno": row.slobodno or 0,
    }


def _reset_demo_u_opcini(db: Session, opcina_naziv: str, dry_run: bool) -> int:
    ids = db.execute(
        text(
            f"""
            SELECT m.id
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE o.naziv = :naziv AND {DEMO_JMBG_WHERE}
            """
        ),
        {"naziv": opcina_naziv},
    ).fetchall()
    if not ids:
        return 0
    id_list = [r.id for r in ids]
    if dry_run:
        return len(id_list)
    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan',
                jmbg = NULL,
                ime = NULL,
                prezime = NULL,
                email = NULL,
                adresa = NULL,
                grad = NULL,
                postanski_broj = NULL,
                datum_dodjele = NULL,
                datum_karantene = NULL,
                karantena_razlog = NULL,
                rezerviran_do = NULL,
                updated_at = NOW()
            WHERE id = ANY(:ids)
            """
        ),
        {"ids": id_list},
    )
    return len(id_list)


def _ukloni_višak_demo(db: Session, opcina_naziv: str, koliko: int, dry_run: bool) -> int:
    if koliko <= 0:
        return 0
    rows = db.execute(
        text(
            f"""
            SELECT m.id
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE o.naziv = :naziv
              AND m.status IN {ZAUZET_STATUS}
              AND {DEMO_JMBG_WHERE}
            ORDER BY m.broj DESC
            LIMIT :limit
            """
        ),
        {"naziv": opcina_naziv, "limit": koliko},
    ).fetchall()
    if not rows:
        return 0
    id_list = [r.id for r in rows]
    if dry_run:
        return len(id_list)
    db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan',
                jmbg = NULL,
                ime = NULL,
                prezime = NULL,
                email = NULL,
                adresa = NULL,
                grad = NULL,
                postanski_broj = NULL,
                datum_dodjele = NULL,
                datum_karantene = NULL,
                karantena_razlog = NULL,
                rezerviran_do = NULL,
                updated_at = NOW()
            WHERE id = ANY(:ids)
            """
        ),
        {"ids": id_list},
    )
    return len(id_list)


def _dodaj_demo_zauzete(
    db: Session,
    opcina_naziv: str,
    koliko: int,
    dry_run: bool,
    jmbg_offset: int,
) -> int:
    if koliko <= 0:
        return 0
    rows = db.execute(
        text(
            f"""
            SELECT m.id, m.broj
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE o.naziv = :naziv AND m.status = 'slobodan'
            ORDER BY m.broj
            LIMIT :limit
            """
        ),
        {"naziv": opcina_naziv, "limit": koliko},
    ).fetchall()
    if len(rows) < koliko:
        print(
            f"  UPozorenje: {opcina_naziv} — traženo {koliko} slobodnih, "
            f"dostupno {len(rows)}"
        )
    if not rows:
        return 0
    if dry_run:
        return len(rows)
    for i, row in enumerate(rows):
        n = jmbg_offset + i + 1
        jmbg = generiraj_demo_jmbg(n)
        db.execute(
            text(
                """
                UPDATE msisdn
                SET status = 'zauzet',
                    ime = 'Demo',
                    prezime = :prezime,
                    jmbg = :jmbg,
                    email = :email,
                    adresa = 'Demo ulica 1',
                    grad = :grad,
                    postanski_broj = '88000',
                    datum_dodjele = NOW(),
                    datum_karantene = NULL,
                    karantena_razlog = NULL,
                    rezerviran_do = NULL,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "prezime": f"Korisnik{n}",
                "jmbg": jmbg,
                "email": f"demo{n}@test.ba",
                "grad": opcina_naziv,
            },
        )
    return len(rows)


def sync_opcina(
    db: Session,
    opcina_naziv: str,
    postotak: float,
    *,
    dry_run: bool,
    jmbg_offset: int,
) -> dict:
    stat = _broj_statistike(db, opcina_naziv)
    ukupno = stat["ukupno"]
    if ukupno == 0:
        print(f"  {opcina_naziv}: nema MSISDN-a — preskačem")
        return {"preskoceno": True, **stat}

    cilj = cilj_zauzeto(ukupno, postotak)
    trenutno = stat["zauzeto"]
    razlika = cilj - trenutno

    print(
        f"  {opcina_naziv}: ukupno={ukupno}, zauzeto={trenutno}, "
        f"cilj={cilj} ({postotak}%), razlika={razlika:+d}"
    )

    uklonjeno = 0
    dodano = 0

    if razlika < 0:
        uklonjeno = _ukloni_višak_demo(db, opcina_naziv, -razlika, dry_run)
        print(f"    -> uklonjeno demo zauzetih: {uklonjeno}")
        if uklonjeno < -razlika:
            print(
                f"    -> UPozorenje: jos {(-razlika) - uklonjeno} viska su "
                "stvarni korisnici — nisu dirani"
            )
    elif razlika > 0:
        dodano = _dodaj_demo_zauzete(db, opcina_naziv, razlika, dry_run, jmbg_offset)
        print(f"    -> dodano demo zauzetih: {dodano}")

    poslije = _broj_statistike(db, opcina_naziv)
    if ukupno > 0:
        stvarni_postotak = round((poslije["zauzeto"] / ukupno) * 100, 2)
        print(f"    -> poslije: zauzeto={poslije['zauzeto']} ({stvarni_postotak}%)")

    return {
        "preskoceno": False,
        "uklonjeno": uklonjeno,
        "dodano": dodano,
        **poslije,
    }


def reset_demo(db: Session, dry_run: bool) -> None:
    print("Reset demo zauzetih u Goražde i Crnići…")
    ukupno = 0
    for naziv, _ in DEMO_CILJEVI:
        n = _reset_demo_u_opcini(db, naziv, dry_run)
        print(f"  {naziv}: {n} redova")
        ukupno += n
    if not dry_run:
        db.commit()
    print(f"Ukupno resetirano: {ukupno}" + (" (dry-run)" if dry_run else ""))


def primijeni(db: Session, dry_run: bool) -> None:
    print("Postavljanje demo zauzetosti…")
    offset = 0
    for naziv, postotak in DEMO_CILJEVI:
        sync_opcina(db, naziv, postotak, dry_run=dry_run, jmbg_offset=offset)
        offset += 10_000
    if not dry_run:
        db.commit()
    print("Gotovo." + (" (dry-run — nema promjena)" if dry_run else ""))


def ispisi_statistike_api(db: Session) -> None:
    from app.services.msisdn_service import statistike

    data = statistike(db)
    for naziv, _ in DEMO_CILJEVI:
        row = next((o for o in data["po_opcini"] if o["naziv"] == naziv), None)
        if row:
            print(
                f"  /statistike -> {naziv}: "
                f"{row['postotak_zauzetosti']}% "
                f"({row['ukupno'] - row['slobodni']} / {row['ukupno']})"
            )
        else:
            print(f"  /statistike -> {naziv}: nije u odgovoru")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Demo zauzetost po općini za dashboard (Goražde 51%, Crnići 91%)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ispiši plan bez UPDATE-a",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Vrati demo zauzete redove na slobodan u ciljnim općinama",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Nakon seeda pošalji email upozorenje za općine s zauzetoscu >= prag (90%%)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            reset_demo(db, args.dry_run)
        else:
            primijeni(db, args.dry_run)
        if not args.dry_run:
            ispisi_statistike_api(db)
        if args.notify:
            if args.dry_run or args.reset:
                print("--notify preskočen (--dry-run ili --reset)")
            else:
                posalji_iskoristivost_obavijest()
    finally:
        db.close()


def posalji_iskoristivost_obavijest() -> None:
    """Pozovi postojeći alert servis i ispiši sažetak (npr. Crnići >= 90%)."""
    from app.services.iskoristivost_alerts import provjeri_iskoristivost_alert

    rez = provjeri_iskoristivost_alert()
    print(
        f"Email upozorenje: {rez['poslano_opcina']} općina iznad {rez['prag']}% "
        f"(SMTP: {'da' if rez['smtp_konfiguriran'] else 'ne'})"
    )
    for o in rez["opce"]:
        print(
            f"  - {o['naziv']}: {o['postotak_zauzetosti']}% "
            f"({o['ukupno'] - o['slobodni']} / {o['ukupno']})"
        )
    if not rez["opce"]:
        print("  (nema općina iznad praga)")


if __name__ == "__main__":
    main()
