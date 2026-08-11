from sqlalchemy import text
from sqlalchemy.orm import Session


def lista_korisnika(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                COALESCE(MAX(m.ime), '') AS ime,
                COALESCE(MAX(m.prezime), '') AS prezime,
                m.jmbg,
                MAX(m.email) AS email,
                COUNT(*)::int AS broj_brojeva,
                COUNT(*) FILTER (WHERE m.status = 'zauzet')::int AS broj_zauzet,
                COUNT(*) FILTER (WHERE m.status = 'karantena')::int AS broj_karantena
            FROM msisdn m
            WHERE m.status IN ('zauzet', 'karantena')
              AND m.jmbg IS NOT NULL
              AND TRIM(m.jmbg) <> ''
            GROUP BY m.jmbg
            ORDER BY MAX(m.prezime), MAX(m.ime)
            """
        )
    ).fetchall()
    return [
        {
            "ime": r.ime or "",
            "prezime": r.prezime or "",
            "jmbg": r.jmbg,
            "email": r.email,
            "broj_brojeva": r.broj_brojeva,
            "broj_zauzet": r.broj_zauzet,
            "broj_karantena": r.broj_karantena,
        }
        for r in rows
    ]


def lokacije_hijerarhija(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT o.naziv AS opcina_naziv, l.id, l.naziv, l.adresa, l.postanski_broj
            FROM opcine o
            JOIN lokacije l ON l.opcina_id = o.id
            ORDER BY o.naziv, l.naziv
            """
        )
    ).fetchall()
    by_opcina: dict[str, list[dict]] = {}
    for r in rows:
        by_opcina.setdefault(r.opcina_naziv, []).append(
            {
                "id": r.id,
                "naziv": r.naziv,
                "postanski_broj": r.postanski_broj,
            }
        )
    return [
        {"opcina_naziv": naziv, "lokacije": lokacije}
        for naziv, lokacije in sorted(by_opcina.items(), key=lambda x: x[0])
    ]


def lista_opcina_sve_sa_brojkom(db: Session, pretraga: str | None = None) -> list[dict]:
    """Sve općine s brojem MSISDN u RAK lancu (0 ako nema brojeva)."""
    params: dict = {}
    naziv_filter = ""
    if pretraga and pretraga.strip():
        naziv_filter = "AND o.naziv ILIKE :pretraga"
        params["pretraga"] = f"%{pretraga.strip()}%"

    rows = db.execute(
        text(
            f"""
            SELECT
                o.id,
                o.naziv,
                o.entitet,
                COALESCE(
                    (
                        SELECT COUNT(m.id)::int
                        FROM lokacije l
                        JOIN uredjaji u ON u.lokacija_id = l.id
                        JOIN rasponi r ON r.uredjaj_id = u.id
                        JOIN msisdn m ON m.raspon_id = r.id
                        WHERE l.opcina_id = o.id
                    ),
                    0
                ) AS broj_msisdn
            FROM opcine o
            WHERE 1=1 {naziv_filter}
            ORDER BY o.naziv ASC, broj_msisdn DESC, o.id ASC
            """
        ),
        params,
    ).fetchall()
    return [
        {
            "id": r.id,
            "naziv": r.naziv,
            "entitet": r.entitet,
            "broj_msisdn": r.broj_msisdn,
        }
        for r in rows
    ]


def lista_opcina_sa_brojevima(db: Session, pretraga: str | None = None) -> list[dict]:
    """Općine koje imaju barem jedan MSISDN (RAK lanac); po nazivu jedan id (najveći broj)."""
    params: dict = {}
    naziv_filter = ""
    if pretraga and pretraga.strip():
        naziv_filter = "AND o.naziv ILIKE :pretraga"
        params["pretraga"] = f"%{pretraga.strip()}%"

    rows = db.execute(
        text(
            f"""
            SELECT o.id, o.naziv, o.entitet, COUNT(m.id)::int AS broj_msisdn
            FROM opcine o
            JOIN lokacije l ON l.opcina_id = o.id
            JOIN uredjaji u ON u.lokacija_id = l.id
            JOIN rasponi r ON r.uredjaj_id = u.id
            JOIN msisdn m ON m.raspon_id = r.id
            WHERE 1=1 {naziv_filter}
            GROUP BY o.id, o.naziv, o.entitet
            HAVING COUNT(m.id) > 0
            ORDER BY o.naziv ASC, COUNT(m.id) DESC
            """
        ),
        params,
    ).fetchall()

    seen_nazivi: set[str] = set()
    result: list[dict] = []
    for r in rows:
        if r.naziv in seen_nazivi:
            continue
        seen_nazivi.add(r.naziv)
        result.append(
            {
                "id": r.id,
                "naziv": r.naziv,
                "entitet": r.entitet,
                "broj_msisdn": r.broj_msisdn,
            }
        )
    return result


def lista_msan_uredjaja(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
                u.id,
                u.oznaka AS naziv,
                o.naziv AS opcina_naziv,
                (
                    SELECT COUNT(*)::int
                    FROM msisdn m
                    JOIN rasponi r ON r.id = m.raspon_id
                    WHERE r.uredjaj_id = u.id
                ) AS kapacitet
            FROM uredjaji u
            JOIN lokacije l ON l.id = u.lokacija_id
            JOIN opcine o ON o.id = l.opcina_id
            WHERE u.tip = 'MSAN'
            ORDER BY o.naziv, u.oznaka
            """
        )
    ).fetchall()
    return [
        {
            "id": r.id,
            "naziv": r.naziv,
            "opcina_naziv": r.opcina_naziv,
            "kapacitet": r.kapacitet or 0,
        }
        for r in rows
    ]
