"""Portal za kupce — registracija, prijava, moji brojevi, ugovor, kontakt."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import KupacKontakt, Radnik
from app.services.dokumenti_service import osiguraj_dokumente
from app.services.jmbg import validiraj_jmbg


def registracija_kupca(
    db: Session,
    *,
    ime: str,
    prezime: str,
    email: str,
    jmbg: str,
    lozinka_hash: str,
) -> Radnik:
    if not validiraj_jmbg(jmbg):
        raise ValueError("jmbg_neispravan")
    postoji_email = db.execute(
        text("SELECT id FROM radnici WHERE email = :email"),
        {"email": email.strip().lower()},
    ).fetchone()
    if postoji_email:
        raise ValueError("email_postoji")
    postoji_jmbg = db.execute(
        text("SELECT id FROM radnici WHERE jmbg = :jmbg AND uloga = 'kupac'"),
        {"jmbg": jmbg},
    ).fetchone()
    if postoji_jmbg:
        raise ValueError("jmbg_postoji")
    kupac = Radnik(
        email=email.strip().lower(),
        ime=ime.strip(),
        prezime=prezime.strip(),
        lozinka_hash=lozinka_hash,
        uloga="kupac",
        aktivan=True,
        jmbg=jmbg,
    )
    db.add(kupac)
    db.commit()
    db.refresh(kupac)
    return kupac


def moji_brojevi(
    db: Session,
    jmbg: str,
    stranica: int = 1,
    velicina: int = 20,
) -> dict:
    offset = max(0, (stranica - 1) * velicina)
    ukupno = db.execute(
        text(
            """
            SELECT COUNT(*)::int
            FROM msisdn m
            WHERE m.jmbg = :jmbg AND m.status IN ('zauzet', 'karantena')
            """
        ),
        {"jmbg": jmbg},
    ).scalar() or 0

    rows = db.execute(
        text(
            """
            SELECT m.id, m.broj, m.status, m.datum_dodjele,
                   COALESCE(k.naziv, 'silver') AS kvaliteta
            FROM msisdn m
            LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE m.jmbg = :jmbg AND m.status IN ('zauzet', 'karantena')
            ORDER BY m.datum_dodjele DESC NULLS LAST, m.broj
            LIMIT :limit OFFSET :offset
            """
        ),
        {"jmbg": jmbg, "limit": velicina, "offset": offset},
    ).fetchall()

    return {
        "ukupno": ukupno,
        "stranica": stranica,
        "velicina_stranice": velicina,
        "brojevi": [
            {
                "id": r.id,
                "broj": r.broj,
                "status": r.status,
                "kvaliteta": r.kvaliteta,
                "datum_dodjele": r.datum_dodjele,
            }
            for r in rows
        ],
    }


def provjeri_pristup_ugovoru(db: Session, msisdn_id: int, jmbg: str) -> bool:
    row = db.execute(
        text("SELECT jmbg FROM msisdn WHERE id = :id"),
        {"id": msisdn_id},
    ).fetchone()
    if not row or not row.jmbg:
        return False
    return row.jmbg == jmbg


def preuzmi_ugovor_pdf(db: Session, msisdn_id: int, jmbg: str) -> bytes:
    if not provjeri_pristup_ugovoru(db, msisdn_id, jmbg):
        raise PermissionError("nema_pristupa")
    return osiguraj_dokumente(db, msisdn_id, "ugovor")


def posalji_kontakt(
    db: Session,
    kupac_id: int,
    predmet: str,
    poruka: str,
) -> KupacKontakt:
    zapis = KupacKontakt(kupac_id=kupac_id, predmet=predmet.strip(), poruka=poruka.strip())
    db.add(zapis)
    db.commit()
    db.refresh(zapis)
    return zapis


def opcionalno_posalji_admin_email(kupac: Radnik, predmet: str, poruka: str) -> None:
    """Šalje obavijest adminu ako je SMTP konfiguriran."""
    if not settings.smtp_enabled:
        return
    try:
        from app.services.email_service import send_email_with_attachment

        body = (
            f"Nova poruka s portala za kupce\n\n"
            f"Od: {kupac.ime} {kupac.prezime} <{kupac.email}>\n"
            f"JMBG: {kupac.jmbg or '—'}\n\n"
            f"Predmet: {predmet}\n\n{poruka}"
        )
        send_email_with_attachment(
            settings.admin_alert_email,
            f"[Portal kupac] {predmet}",
            body,
        )
    except Exception:
        pass
