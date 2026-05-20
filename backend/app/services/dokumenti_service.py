from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.contract_pdf import generiraj_pdf_ugovor
from app.services.document_storage import spremi_racun, spremi_ugovor, racun_path, ugovor_path
from app.services.invoice_email import generiraj_pdf_racun
from app.services.pdf_fonts import assert_pdf_has_dejavu
from app.services.phone import formatiraj_broj


def _ucitaj_msisdn_podatke(db: Session, msisdn_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT m.id, m.broj, m.ime, m.prezime, m.jmbg, m.email,
                   m.adresa, m.grad, m.postanski_broj,
                   k.naziv AS kvaliteta, k.cijena
            FROM msisdn m
            LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE m.id = :id
            """
        ),
        {"id": msisdn_id},
    ).fetchone()
    if not row:
        raise ValueError(f"MSISDN {msisdn_id} nije pronađen.")
    return {
        "id": row.id,
        "broj": row.broj,
        "broj_formatiran": formatiraj_broj(row.broj),
        "ime": row.ime or "",
        "prezime": row.prezime or "",
        "jmbg": row.jmbg or "",
        "email": row.email or "",
        "adresa": row.adresa or "",
        "grad": row.grad or "",
        "postanski_broj": row.postanski_broj or "",
        "kvaliteta": row.kvaliteta or "silver",
        "cijena": float(row.cijena or 10),
    }


def generiraj_i_spremi_dokumente(db: Session, msisdn_id: int) -> None:
    pod = _ucitaj_msisdn_podatke(db, msisdn_id)
    racun_pdf = generiraj_pdf_racun(
        pod["ime"],
        pod["prezime"],
        pod["jmbg"],
        pod["email"],
        pod["broj_formatiran"],
        pod["kvaliteta"],
        pod["cijena"],
        adresa=pod["adresa"],
        grad=pod["grad"],
        postanski_broj=pod["postanski_broj"],
    )
    from app.config import settings

    portal_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
    ugovor_pdf = generiraj_pdf_ugovor(
        ime=pod["ime"],
        prezime=pod["prezime"],
        jmbg=pod["jmbg"],
        adresa=pod["adresa"],
        grad=pod["grad"],
        postanski_broj=pod["postanski_broj"],
        broj_formatiran=pod["broj_formatiran"],
        kvaliteta_naziv=pod["kvaliteta"],
        cijena=pod["cijena"],
        msisdn_id=msisdn_id,
        portal_base_url=portal_url,
    )
    assert_pdf_has_dejavu(racun_pdf, "Račun")
    assert_pdf_has_dejavu(ugovor_pdf, "Ugovor")
    spremi_racun(msisdn_id, racun_pdf)
    spremi_ugovor(msisdn_id, ugovor_pdf)


def osiguraj_dokumente(db: Session, msisdn_id: int, vrsta: str) -> bytes:
    """Uvijek regenerira PDF pri GET (ne servira zastarjeli Helvetica cache)."""
    generiraj_i_spremi_dokumente(db, msisdn_id)
    path = racun_path(msisdn_id) if vrsta == "racun" else ugovor_path(msisdn_id)
    pdf_bytes = path.read_bytes()
    assert_pdf_has_dejavu(pdf_bytes, path.name)
    return pdf_bytes
