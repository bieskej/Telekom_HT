import logging
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Kvaliteta, Msisdn, MsisdnHistory
from app.services.jmbg import validiraj_jmbg
from app.services.phone import formatiraj_broj

logger = logging.getLogger(__name__)

SLOBODAN_UVJET = """
    m.status = 'slobodan'
    AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
"""

OPCINA_JOIN = """
    JOIN rasponi r ON r.id = m.raspon_id
    JOIN uredjaji u ON u.id = r.uredjaj_id
    JOIN lokacije l ON l.id = u.lokacija_id
    JOIN opcine o ON o.id = l.opcina_id
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_silver_id(db: Session) -> int:
    row = db.execute(select(Kvaliteta.id).where(Kvaliteta.naziv == "silver")).scalar_one()
    return row


def _log_history(
    db: Session,
    msisdn_id: int,
    stari_status: str | None,
    novi_status: str,
    akcija: str,
    napomena: str | None = None,
    radnik_id: int | None = None,
) -> None:
    db.add(
        MsisdnHistory(
            msisdn_id=msisdn_id,
            stari_status=stari_status,
            novi_status=novi_status,
            akcija=akcija,
            napomena=napomena,
            radnik_id=radnik_id,
        )
    )


def _datum_isteka_karantene(msisdn: Msisdn) -> datetime | None:
    if not msisdn.datum_karantene:
        return None
    return msisdn.datum_karantene + timedelta(days=msisdn.karantena_dana or 0)


def _provjeri_diamond_ovlast(kval: Kvaliteta, radnik_uloga: str | None) -> None:
    if kval.naziv == "diamond" and radnik_uloga != "admin":
        raise HTTPException(
            status_code=403,
            detail="Diamond kategorija dostupna je samo administratorima.",
        )


def _resolve_kvaliteta(db: Session, kvaliteta_id: int | None, radnik_uloga: str | None) -> Kvaliteta:
    if kvaliteta_id:
        kval = db.get(Kvaliteta, kvaliteta_id)
        if not kval:
            raise HTTPException(status_code=404, detail="Kvaliteta nije pronađena.")
        _provjeri_diamond_ovlast(kval, radnik_uloga)
        return kval
    kval = db.execute(select(Kvaliteta).where(Kvaliteta.naziv == "silver")).scalar_one()
    return kval


def _resolve_kvaliteta_by_naziv(db: Session, kvaliteta_naziv: str, radnik_uloga: str | None) -> Kvaliteta:
    naziv = (kvaliteta_naziv or "silver").lower().strip()
    kval = db.execute(select(Kvaliteta).where(Kvaliteta.naziv == naziv)).scalar_one_or_none()
    if not kval:
        raise HTTPException(status_code=404, detail=f"Kvaliteta '{naziv}' nije pronađena.")
    _provjeri_diamond_ovlast(kval, radnik_uloga)
    return kval


def _kvaliteta_iz_msisdn(db: Session, msisdn: Msisdn) -> Kvaliteta:
    """Kvaliteta broja u bazi (inherentna); ne iz forme."""
    if msisdn.kvaliteta_id:
        kval = db.get(Kvaliteta, msisdn.kvaliteta_id)
        if kval:
            return kval
    return db.execute(select(Kvaliteta).where(Kvaliteta.naziv == "silver")).scalar_one()


def _provjeri_kvaliteta_odgovara(msisdn: Msisdn, trazena: Kvaliteta) -> None:
    if msisdn.kvaliteta_id != trazena.id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Rezervirani broj nije kategorije {trazena.naziv}. "
                "Odaberite odgovarajuću kvalitetu ili ponovno rezervirajte broj."
            ),
        )


def _raise_nema_slobodnih(db: Session, opcina_naziv: str, kvaliteta_id: int | None) -> None:
    zup_oznaka = db.execute(
        text(
            """
            SELECT z.oznaka FROM opcine o
            LEFT JOIN zupanije z ON z.id = o.zupanija_id
            WHERE o.naziv = :n
            LIMIT 1
            """
        ),
        {"n": opcina_naziv},
    ).scalar()
    zup_dio = f" niti u županijskom poolu {zup_oznaka}" if zup_oznaka else ""

    if kvaliteta_id is not None:
        kval = db.get(Kvaliteta, kvaliteta_id)
        naziv = kval.naziv if kval else "tražene kvalitete"
        raise HTTPException(
            status_code=404,
            detail=f"Nema slobodnih {naziv} brojeva za općinu {opcina_naziv}{zup_dio}.",
        )
    raise HTTPException(
        status_code=404,
        detail=f"Nema slobodnih brojeva za općinu {opcina_naziv}{zup_dio}.",
    )


def _zakljucaj_rezervirani_msisdn(db: Session, msisdn_id: int, opcina_naziv: str) -> Msisdn:
    """Provjeri i zaključaj broj rezerviran za dodjelu (status slobodan, aktivna rezervacija).

    Prvi pokušaj: broj točno u traženoj općini. Ako ne valja, dopusti broj iz
    iste županije (županijski pool – kompatibilno s `_find_slobodan_ids`).
    """
    row = db.execute(
        text(
            f"""
            SELECT m.id
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE m.id = :msisdn_id
              AND o.naziv = :opcina_naziv
              AND m.status = 'slobodan'
              AND m.rezerviran_do IS NOT NULL
              AND m.rezerviran_do > NOW()
            FOR UPDATE OF m
            """
        ),
        {"msisdn_id": msisdn_id, "opcina_naziv": opcina_naziv},
    ).fetchone()
    msisdn: Msisdn | None
    if row:
        msisdn = db.get(Msisdn, msisdn_id)
    else:
        msisdn = _zakljucaj_rezervirani_msisdn_zupanija(db, msisdn_id, opcina_naziv)
    if not msisdn:
        raise HTTPException(
            status_code=400,
            detail=(
                "Broj nije valjan za dodjelu: mora biti slobodan, aktivno rezerviran "
                "i u odabranoj općini ili istoj županiji."
            ),
        )
    return msisdn


def _find_slobodan_ids(
    db: Session,
    opcina_naziv: str,
    limit: int,
    kvaliteta_id: int | None = None,
    fallback_zupanija: bool = True,
) -> list[int]:
    """Vrati ID-ove slobodnih brojeva za općinu (s rezerviranim filterom).

    Prvi pokušaj: točno `o.naziv = :opcina_naziv`. Ako ne nađe ništa i
    `fallback_zupanija=True`, traži u svim općinama iste županije
    (županijski pool – npr. korisnik iz Čapljine dobiva broj iz HNŽ poola
    ako u Čapljini nema slobodnih).
    """
    kval_filter = ""
    params: dict = {"opcina_naziv": opcina_naziv, "limit": limit}
    if kvaliteta_id is not None:
        kval_filter = "AND m.kvaliteta_id = :kvaliteta_id"
        params["kvaliteta_id"] = kvaliteta_id
    sql = text(
        f"""
        SELECT m.id
        FROM msisdn m
        {OPCINA_JOIN}
        WHERE o.naziv = :opcina_naziv
          AND {SLOBODAN_UVJET}
          {kval_filter}
        ORDER BY m.broj
        LIMIT :limit
        FOR UPDATE OF m SKIP LOCKED
        """
    )
    rows = db.execute(sql, params).fetchall()
    ids = [r[0] for r in rows]
    if ids or not fallback_zupanija:
        return ids

    sql_zup = text(
        f"""
        SELECT m.id
        FROM msisdn m
        {OPCINA_JOIN}
        WHERE o.zupanija_id = (
                SELECT zupanija_id FROM opcine WHERE naziv = :opcina_naziv LIMIT 1
              )
          AND {SLOBODAN_UVJET}
          {kval_filter}
        ORDER BY m.broj
        LIMIT :limit
        FOR UPDATE OF m SKIP LOCKED
        """
    )
    rows_zup = db.execute(sql_zup, params).fetchall()
    return [r[0] for r in rows_zup]


def _zakljucaj_rezervirani_msisdn_zupanija(db: Session, msisdn_id: int, opcina_naziv: str) -> Msisdn | None:
    """Fallback: dohvati rezervirani broj u istoj županiji kao tražena općina."""
    row = db.execute(
        text(
            f"""
            SELECT m.id
            FROM msisdn m
            {OPCINA_JOIN}
            WHERE m.id = :msisdn_id
              AND o.zupanija_id = (
                    SELECT zupanija_id FROM opcine WHERE naziv = :opcina_naziv LIMIT 1
                  )
              AND m.status = 'slobodan'
              AND m.rezerviran_do IS NOT NULL
              AND m.rezerviran_do > NOW()
            FOR UPDATE OF m
            """
        ),
        {"msisdn_id": msisdn_id, "opcina_naziv": opcina_naziv},
    ).fetchone()
    if not row:
        return None
    return db.get(Msisdn, msisdn_id)


def dodijeli_broj(
    db: Session,
    opcina_naziv: str,
    ime: str,
    prezime: str,
    jmbg: str,
    email: str,
    adresa: str,
    grad: str,
    postanski_broj: str,
    background_tasks: BackgroundTasks | None = None,
    msisdn_id: int | None = None,
    kvaliteta_id: int | None = None,
    radnik_uloga: str | None = None,
    placanje: dict | None = None,
) -> dict:
    if not validiraj_jmbg(jmbg):
        raise HTTPException(status_code=400, detail="JMBG nije validan (modul 11).")

    kval_trazena = _resolve_kvaliteta(db, kvaliteta_id, radnik_uloga)
    sada = _utcnow()

    if msisdn_id is not None:
        msisdn = _zakljucaj_rezervirani_msisdn(db, msisdn_id, opcina_naziv)
        _provjeri_kvaliteta_odgovara(msisdn, kval_trazena)
    else:
        ids = _find_slobodan_ids(db, opcina_naziv, 1, kval_trazena.id)
        if not ids:
            _raise_nema_slobodnih(db, opcina_naziv, kval_trazena.id)
        msisdn_id = ids[0]
        msisdn = db.get(Msisdn, msisdn_id)
        if not msisdn:
            raise HTTPException(status_code=404, detail="Broj nije pronađen.")

    kval = _kvaliteta_iz_msisdn(db, msisdn)
    stari_status = msisdn.status

    msisdn.status = "zauzet"
    msisdn.ime = ime
    msisdn.prezime = prezime
    msisdn.jmbg = jmbg
    msisdn.email = email
    msisdn.adresa = adresa
    msisdn.grad = grad
    msisdn.postanski_broj = postanski_broj
    msisdn.datum_dodjele = sada
    msisdn.rezerviran_do = None
    msisdn.updated_at = sada

    _log_history(db, msisdn_id, stari_status, "zauzet", "dodjela", f"Dodjela za {ime} {prezime}")
    cijena = float(kval.cijena)

    placanje_status = None
    if placanje:
        from app.services.placanje_service import kreiraj_placanje

        pl = kreiraj_placanje(
            db,
            msisdn.id,
            placanje.get("nacin", "gotovina"),
            cijena,
            broj_kartice=placanje.get("broj_kartice"),
            datum_isteka=placanje.get("datum_isteka"),
            cvv=placanje.get("cvv"),
            ime_vlasnika=placanje.get("ime_vlasnika"),
        )
        placanje_status = pl.status

    db.commit()
    db.refresh(msisdn)

    from app.services.dokumenti_service import generiraj_i_spremi_dokumente

    generiraj_i_spremi_dokumente(db, msisdn.id)

    broj_fmt = formatiraj_broj(msisdn.broj)
    nacin_placanja = placanje.get("nacin") if placanje else None

    if background_tasks and email and email.strip():
        from app.services.email_notifications import obradi_dodjelu_email_html

        background_tasks.add_task(
            obradi_dodjelu_email_html,
            msisdn.id,
            ime,
            prezime,
            email,
            broj_fmt,
            kval.naziv,
            adresa=adresa,
            grad=grad,
            postanski_broj=postanski_broj,
        )

    return {
        "msisdn_id": msisdn.id,
        "broj": msisdn.broj,
        "broj_formatiran": broj_fmt,
        "status": msisdn.status,
        "kvaliteta": kval.naziv,
        "cijena": cijena,
        "email_poslan": settings.smtp_enabled,
        "racun_url": f"/msisdn/{msisdn.id}/racun",
        "ugovor_url": f"/msisdn/{msisdn.id}/ugovor",
        "placanje_status": placanje_status,
    }


def oslobodi_broj(db: Session, msisdn_id: int, karantena_dana: int | None) -> dict:
    dana = karantena_dana if karantena_dana is not None else settings.karantena_dana_default
    msisdn = db.get(Msisdn, msisdn_id)
    if not msisdn:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")
    if msisdn.status != "zauzet":
        raise HTTPException(status_code=400, detail="Broj mora biti u statusu 'zauzet'.")

    stari = msisdn.status
    sada = _utcnow()
    msisdn.status = "karantena"
    msisdn.datum_karantene = sada
    msisdn.karantena_dana = dana
    msisdn.rezerviran_do = None
    msisdn.updated_at = sada

    _log_history(db, msisdn_id, stari, "karantena", "oslobadanje")
    db.commit()

    from app.services.email_notifications import posalji_email_karantena_start

    posalji_email_karantena_start(
        db,
        msisdn_id,
        msisdn.email,
        msisdn.ime,
        msisdn.prezime,
        msisdn.broj,
        msisdn.datum_karantene,
        dana,
    )

    return {
        "poruka": "Broj je uspješno stavljen u karantenu.",
        "msisdn_id": msisdn_id,
        "status": "karantena",
        "karantena_dana": dana,
    }


def azuriraj_karantenu(
    db: Session,
    msisdn_id: int,
    *,
    produzi_dana: int | None = None,
    skrati_dana: int | None = None,
    razlog: str | None = None,
    radnik_uloga: str,
) -> dict:
    if produzi_dana is not None and skrati_dana is not None:
        raise HTTPException(status_code=400, detail="Odaberite samo produženje ili skraćivanje.")
    if produzi_dana is None and skrati_dana is None:
        raise HTTPException(status_code=400, detail="Navedite produzi_dana ili skrati_dana.")

    msisdn = db.get(Msisdn, msisdn_id)
    if not msisdn:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")
    if msisdn.status != "karantena":
        raise HTTPException(status_code=400, detail="Broj mora biti u statusu 'karantena'.")

    if skrati_dana is not None:
        if radnik_uloga != "admin":
            raise HTTPException(status_code=403, detail="Skraćivanje karantene dozvoljeno je samo administratorima.")
        nova_dana = msisdn.karantena_dana - skrati_dana
        if nova_dana < 1:
            raise HTTPException(status_code=400, detail="Karantena mora trajati najmanje 1 dan.")
        msisdn.karantena_dana = nova_dana
    else:
        produzi = produzi_dana or 0
        if produzi < 1 or produzi > 180:
            raise HTTPException(status_code=400, detail="produzi_dana mora biti između 1 i 180.")
        msisdn.karantena_dana = min(msisdn.karantena_dana + produzi, 180)

    if razlog is not None:
        msisdn.karantena_razlog = razlog.strip() or None
    msisdn.updated_at = _utcnow()
    _log_history(db, msisdn_id, "karantena", "karantena", "karantena_azurirana", razlog)
    db.commit()
    db.refresh(msisdn)

    istek = _datum_isteka_karantene(msisdn)
    return {
        "msisdn_id": msisdn_id,
        "karantena_dana": msisdn.karantena_dana,
        "datum_karantene": msisdn.datum_karantene,
        "datum_isteka": istek,
        "karantena_razlog": msisdn.karantena_razlog,
    }


def oslobodi_iz_karantene_admin(
    db: Session,
    msisdn_id: int,
    razlog: str | None,
    radnik_id: int,
) -> dict:
    msisdn = db.get(Msisdn, msisdn_id)
    if not msisdn:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")
    if msisdn.status != "karantena":
        raise HTTPException(status_code=400, detail="Broj mora biti u statusu 'karantena'.")

    stari = msisdn.status
    email = msisdn.email
    ime = msisdn.ime
    prezime = msisdn.prezime
    broj = msisdn.broj

    msisdn.status = "slobodan"
    msisdn.datum_karantene = None
    msisdn.karantena_razlog = None
    msisdn.jmbg = None
    msisdn.ime = None
    msisdn.prezime = None
    msisdn.email = None
    msisdn.adresa = None
    msisdn.grad = None
    msisdn.postanski_broj = None
    msisdn.datum_dodjele = None
    msisdn.rezerviran_do = None
    msisdn.updated_at = _utcnow()

    napomena = razlog.strip() if razlog else "Admin oslobađanje iz karantene"
    _log_history(
        db,
        msisdn_id,
        stari,
        "slobodan",
        "oslobodeno_iz_karantene",
        napomena,
        radnik_id=radnik_id,
    )
    db.commit()

    from app.services.email_notifications import posalji_email_karantena_end

    posalji_email_karantena_end(db, msisdn_id, email, ime, prezime, broj)

    return {
        "poruka": "Broj je oslobođen iz karantene i ponovno je slobodan.",
        "msisdn_id": msisdn_id,
        "status": "slobodan",
    }


def dohvati_msisdn_detalj(db: Session, msisdn_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT m.id, m.broj, m.status, m.datum_karantene, m.karantena_dana, m.karantena_razlog,
                   m.jmbg, m.ime, m.prezime, m.email, m.datum_dodjele,
                   k.id AS kvaliteta_id, k.naziv AS kvaliteta, k.cijena,
                   o.naziv AS opcina_naziv
            FROM msisdn m
            LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
            LEFT JOIN rasponi r ON r.id = m.raspon_id
            LEFT JOIN uredjaji u ON u.id = r.uredjaj_id
            LEFT JOIN lokacije l ON l.id = u.lokacija_id
            LEFT JOIN opcine o ON o.id = l.opcina_id
            WHERE m.id = :id
            """
        ),
        {"id": msisdn_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")

    istek = None
    if row.datum_karantene and row.karantena_dana:
        istek = row.datum_karantene + timedelta(days=row.karantena_dana)

    return {
        "id": row.id,
        "broj": row.broj,
        "broj_formatiran": formatiraj_broj(row.broj),
        "status": row.status,
        "datum_karantene": row.datum_karantene,
        "karantena_dana": row.karantena_dana,
        "karantena_razlog": row.karantena_razlog,
        "datum_isteka": istek,
        "jmbg": row.jmbg,
        "ime": row.ime,
        "prezime": row.prezime,
        "email": row.email,
        "datum_dodjele": row.datum_dodjele,
        "kvaliteta_id": row.kvaliteta_id,
        "kvaliteta": row.kvaliteta,
        "cijena": float(row.cijena) if row.cijena is not None else None,
        "opcina_naziv": row.opcina_naziv,
    }


def rezerviraj_broj(db: Session, msisdn_id: int) -> dict:
    msisdn = db.get(Msisdn, msisdn_id)
    if not msisdn:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")
    if msisdn.status != "slobodan":
        raise HTTPException(status_code=400, detail="Mogu se rezervirati samo slobodni brojevi.")

    rezervacija_do = _utcnow() + timedelta(minutes=settings.rezervacija_minuta)
    msisdn.rezerviran_do = rezervacija_do
    msisdn.updated_at = _utcnow()
    db.commit()

    preostalo = int((rezervacija_do - _utcnow()).total_seconds())
    broj_fmt = formatiraj_broj(msisdn.broj)
    return {
        "msisdn_id": msisdn_id,
        "preostalo_sekundi": max(preostalo, 0),
        "broj": msisdn.broj,
        "broj_formatiran": broj_fmt,
    }


def rezerviraj_sljedeci_opcina(
    db: Session,
    opcina_naziv: str,
    kvaliteta_id: int | None = None,
    kvaliteta_naziv: str | None = None,
    radnik_uloga: str | None = None,
) -> dict:
    """Rezervira prvi slobodan broj u općini s traženom inherentnom kvalitetom."""
    if kvaliteta_id is not None:
        kval = _resolve_kvaliteta(db, kvaliteta_id, radnik_uloga)
    elif kvaliteta_naziv:
        kval = _resolve_kvaliteta_by_naziv(db, kvaliteta_naziv, radnik_uloga)
    else:
        kval = _resolve_kvaliteta(db, None, radnik_uloga)

    ids = _find_slobodan_ids(db, opcina_naziv, 1, kval.id)
    if not ids:
        _raise_nema_slobodnih(db, opcina_naziv, kval.id)
    return rezerviraj_broj(db, ids[0])


def ponisti_rezervaciju(db: Session, msisdn_id: int) -> dict:
    msisdn = db.get(Msisdn, msisdn_id)
    if not msisdn:
        raise HTTPException(status_code=404, detail="Broj nije pronađen.")
    msisdn.rezerviran_do = None
    msisdn.updated_at = _utcnow()
    db.commit()
    return {"poruka": "Rezervacija je poništena.", "msisdn_id": msisdn_id}


def dodijeli_bulk(
    db: Session,
    opcina_naziv: str,
    broj_brojeva: int,
    korisnik_ime: str,
    korisnik_prezime: str,
    korisnik_jmbg: str,
    korisnik_email: str,
    adresa: str,
    grad: str,
    postanski_broj: str,
    kvaliteta_naziv: str = "silver",
    radnik_uloga: str | None = None,
    background_tasks: BackgroundTasks | None = None,
    placanje: dict | None = None,
) -> dict:
    if not validiraj_jmbg(korisnik_jmbg):
        raise HTTPException(status_code=400, detail="JMBG nije validan (modul 11).")

    kval = _resolve_kvaliteta_by_naziv(db, kvaliteta_naziv, radnik_uloga)

    ids = _find_slobodan_ids(db, opcina_naziv, broj_brojeva, kval.id)
    if len(ids) < broj_brojeva:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nema dovoljno slobodnih {kval.naziv} brojeva za općinu {opcina_naziv}. "
                f"Dostupno: {len(ids)}, traženo: {broj_brojeva}."
            ),
        )
    sada = _utcnow()
    rezervacija_do = sada + timedelta(minutes=settings.rezervacija_minuta)
    brojevi: list[str] = []
    formatirani: list[str] = []
    msisdn_ids: list[int] = []
    cijena_po_komadu = float(kval.cijena)

    for msisdn_id in ids:
        msisdn = db.get(Msisdn, msisdn_id)
        if not msisdn:
            continue
        stari = msisdn.status
        msisdn.rezerviran_do = rezervacija_do
        db.flush()
        msisdn.status = "zauzet"
        msisdn.ime = korisnik_ime
        msisdn.prezime = korisnik_prezime
        msisdn.jmbg = korisnik_jmbg
        msisdn.email = korisnik_email
        msisdn.adresa = adresa
        msisdn.grad = grad
        msisdn.postanski_broj = postanski_broj
        msisdn.datum_dodjele = sada
        msisdn.rezerviran_do = None
        msisdn.updated_at = sada
        _log_history(
            db,
            msisdn_id,
            stari,
            "zauzet",
            "dodjela",
            f"Bulk dodjela ({kval.naziv}) za {korisnik_ime} {korisnik_prezime}",
        )
        brojevi.append(msisdn.broj)
        formatirani.append(formatiraj_broj(msisdn.broj))
        msisdn_ids.append(msisdn_id)

    dodijeljeno = len(brojevi)
    ukupna_cijena = round(cijena_po_komadu * dodijeljeno, 2)

    placanje_status = None
    if placanje and msisdn_ids:
        from app.services.placanje_service import kreiraj_placanje

        pl = kreiraj_placanje(
            db,
            msisdn_ids[0],
            placanje.get("nacin", "gotovina"),
            ukupna_cijena,
            broj_kartice=placanje.get("broj_kartice"),
            datum_isteka=placanje.get("datum_isteka"),
            cvv=placanje.get("cvv"),
            ime_vlasnika=placanje.get("ime_vlasnika"),
        )
        placanje_status = pl.status

    db.commit()

    from app.services.dokumenti_service import generiraj_i_spremi_dokumente

    stavke = []
    for mid, broj_fmt in zip(msisdn_ids, formatirani, strict=True):
        generiraj_i_spremi_dokumente(db, mid)
        stavke.append(
            {
                "msisdn_id": mid,
                "broj_formatiran": broj_fmt,
                "racun_url": f"/msisdn/{mid}/racun",
                "ugovor_url": f"/msisdn/{mid}/ugovor",
            }
        )

    prvi_msisdn_id = msisdn_ids[0] if msisdn_ids else None
    nacin_placanja = placanje.get("nacin") if placanje else None

    if background_tasks and prvi_msisdn_id and dodijeljeno:
        from app.services.invoice_email import obradi_bulk_dodjelu_email

        background_tasks.add_task(
            obradi_bulk_dodjelu_email,
            prvi_msisdn_id,
            korisnik_ime,
            korisnik_prezime,
            korisnik_jmbg,
            korisnik_email,
            formatirani,
            kval.naziv,
            cijena_po_komadu,
            dodijeljeno,
        )

    return {
        "dodijeljeno": dodijeljeno,
        "brojevi": brojevi,
        "brojevi_formatirani": formatirani,
        "msisdn_ids": msisdn_ids,
        "stavke": stavke,
        "kvaliteta": kval.naziv,
        "cijena_po_komadu": cijena_po_komadu,
        "ukupna_cijena": ukupna_cijena,
        "email_poslan": settings.smtp_enabled,
        "placanje_status": placanje_status,
    }


def _uzorak_u_like(uzorak: str) -> str:
    """Pretvara * u % i ? u _ za SQL LIKE."""
    escaped = uzorak.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped.replace("*", "%").replace("?", "_")


def pretrazi_wildcard(
    db: Session,
    uzorak: str,
    opcina_naziv: str | None,
    kvaliteta_id: int | None,
    limit: int,
) -> dict:
    if not uzorak or not uzorak.strip():
        raise HTTPException(status_code=400, detail="Uzorak je obavezan.")
    like_pat = _uzorak_u_like(uzorak.strip())
    if like_pat.replace("%", "").replace("_", "") == "":
        raise HTTPException(status_code=400, detail="Uzorak je preširok.")

    conditions = [SLOBODAN_UVJET.replace("m.", "m."), "m.broj LIKE :like_pat"]
    params: dict = {"like_pat": like_pat, "limit": min(limit, 100)}

    if opcina_naziv and opcina_naziv.strip():
        conditions.append("o.naziv ILIKE :opcina_naziv")
        params["opcina_naziv"] = f"%{opcina_naziv.strip()}%"
    if kvaliteta_id is not None:
        conditions.append("m.kvaliteta_id = :kvaliteta_id")
        params["kvaliteta_id"] = kvaliteta_id

    where = " AND ".join(conditions)
    rows = db.execute(
        text(
            f"""
            SELECT m.id, m.broj, k.naziv AS kvaliteta, k.cijena, o.naziv AS opcina_naziv
            FROM msisdn m
            {OPCINA_JOIN}
            JOIN kvaliteta k ON k.id = m.kvaliteta_id
            WHERE {where}
            ORDER BY k.cijena DESC, m.broj
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()

    rezultati = [
        {
            "id": r.id,
            "broj": r.broj,
            "broj_formatiran": formatiraj_broj(r.broj),
            "kvaliteta": r.kvaliteta,
            "cijena": float(r.cijena),
            "opcina_naziv": r.opcina_naziv,
        }
        for r in rows
    ]
    return {"uzorak": uzorak, "ukupno": len(rezultati), "rezultati": rezultati}


def pretrazi_msisdn(
    db: Session,
    broj: str | None,
    status: str | None,
    opcina_id: int | None,
    opcina_naziv: str | None,
    uredjaj_id: int | None,
    lokacija_id: int | None,
    korisnik_jmbg: str | None,
    korisnik_ime_prezime: str | None,
    kvaliteta: str | None,
    page: int,
    per_page: int,
) -> dict:
    conditions = ["1=1"]
    params: dict = {"limit": per_page, "offset": (page - 1) * per_page}

    if broj:
        conditions.append("m.broj LIKE :broj")
        params["broj"] = f"%{broj}%"
    if status:
        conditions.append("m.status = :status")
        params["status"] = status
    if opcina_id:
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM rasponi r_geo
                JOIN uredjaji u_geo ON u_geo.id = r_geo.uredjaj_id
                JOIN lokacije l_geo ON l_geo.id = u_geo.lokacija_id
                JOIN opcine o_geo ON o_geo.id = l_geo.opcina_id
                WHERE m.raspon_id = r_geo.id AND o_geo.id = :opcina_id
            )
            """
        )
        params["opcina_id"] = opcina_id
    elif opcina_naziv and opcina_naziv.strip():
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM rasponi r_geo
                JOIN uredjaji u_geo ON u_geo.id = r_geo.uredjaj_id
                JOIN lokacije l_geo ON l_geo.id = u_geo.lokacija_id
                JOIN opcine o_geo ON o_geo.id = l_geo.opcina_id
                WHERE m.raspon_id = r_geo.id AND o_geo.naziv ILIKE :opcina_naziv
            )
            """
        )
        params["opcina_naziv"] = f"%{opcina_naziv.strip()}%"
    if uredjaj_id:
        conditions.append(
            """
            EXISTS (
                SELECT 1 FROM rasponi r_geo
                WHERE m.raspon_id = r_geo.id AND r_geo.uredjaj_id = :uredjaj_id
            )
            """
        )
        params["uredjaj_id"] = uredjaj_id
    if lokacija_id:
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM rasponi r_geo
                JOIN uredjaji u_geo ON u_geo.id = r_geo.uredjaj_id
                WHERE m.raspon_id = r_geo.id AND u_geo.lokacija_id = :lokacija_id
            )
            """
        )
        params["lokacija_id"] = lokacija_id
    if korisnik_jmbg:
        conditions.append("m.jmbg = :jmbg")
        params["jmbg"] = korisnik_jmbg
    if korisnik_ime_prezime:
        term = f"%{korisnik_ime_prezime.strip()}%"
        conditions.append("(m.ime ILIKE :ime_prez OR m.prezime ILIKE :ime_prez)")
        params["ime_prez"] = term
    if kvaliteta:
        conditions.append("k.naziv = :kvaliteta")
        params["kvaliteta"] = kvaliteta

    where = " AND ".join(conditions)
    count_sql = text(
        f"""
        SELECT COUNT(*)
        FROM msisdn m
        LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
        LEFT JOIN rasponi r ON r.id = m.raspon_id
        LEFT JOIN uredjaji u ON u.id = r.uredjaj_id
        LEFT JOIN lokacije l ON l.id = u.lokacija_id
        LEFT JOIN opcine o ON o.id = l.opcina_id
        WHERE {where}
        """
    )
    data_sql = text(
        f"""
        SELECT m.id, m.broj, m.status, o.id AS opcina_id, o.naziv AS opcina_naziv,
               u.id AS uredjaj_id, m.jmbg, k.naziv AS kvaliteta, m.ime, m.prezime, m.email
        FROM msisdn m
        LEFT JOIN kvaliteta k ON k.id = m.kvaliteta_id
        LEFT JOIN rasponi r ON r.id = m.raspon_id
        LEFT JOIN uredjaji u ON u.id = r.uredjaj_id
        LEFT JOIN lokacije l ON l.id = u.lokacija_id
        LEFT JOIN opcine o ON o.id = l.opcina_id
        WHERE {where}
        ORDER BY m.broj
        LIMIT :limit OFFSET :offset
        """
    )

    ukupno = db.execute(count_sql, params).scalar() or 0
    rows = db.execute(data_sql, params).fetchall()

    rezultati = [
        {
            "id": r.id,
            "broj": r.broj,
            "broj_formatiran": formatiraj_broj(r.broj),
            "status": r.status,
            "opcina_id": r.opcina_id,
            "opcina_naziv": r.opcina_naziv,
            "uredjaj_id": r.uredjaj_id,
            "jmbg": r.jmbg,
            "kvaliteta": r.kvaliteta,
            "kvaliteta_naziv": r.kvaliteta,
            "ime": r.ime,
            "prezime": r.prezime,
            "email": r.email,
        }
        for r in rows
    ]

    return {
        "ukupno": ukupno,
        "stranica": page,
        "po_stranici": per_page,
        "rezultati": rezultati,
    }


def statistike(db: Session) -> dict:
    totals = db.execute(
        text(
            """
            SELECT
              COUNT(*) AS ukupno,
              COUNT(*) FILTER (WHERE status = 'slobodan') AS slobodni,
              COUNT(*) FILTER (WHERE status = 'zauzet') AS zauzeti,
              COUNT(*) FILTER (WHERE status = 'karantena') AS karantena
            FROM msisdn
            """
        )
    ).one()

    ukupno = totals.ukupno or 0
    zauzeti = totals.zauzeti or 0
    karantena = totals.karantena or 0
    iskoristivost = round(((zauzeti + karantena) / ukupno) * 100, 2) if ukupno else 0.0

    po_opcini_rows = db.execute(
        text(
            f"""
            SELECT o.naziv,
                   MAX(o.lat) AS lat,
                   MAX(o.lon) AS lon,
                   COUNT(m.id) AS ukupno,
                   COUNT(m.id) FILTER (
                     WHERE m.status = 'slobodan'
                       AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
                   ) AS slobodni,
                   COUNT(m.id) FILTER (WHERE m.status IN ('zauzet', 'karantena')) AS zauzeto_karantena
            FROM msisdn m
            {OPCINA_JOIN}
            GROUP BY o.naziv
            ORDER BY o.naziv
            """
        )
    ).fetchall()

    po_opcini = []
    for r in po_opcini_rows:
        uk = r.ukupno or 0
        zk = r.zauzeto_karantena or 0
        postotak = round((zk / uk) * 100, 2) if uk else 0.0
        po_opcini.append(
            {
                "naziv": r.naziv,
                "postotak_zauzetosti": postotak,
                "slobodni": r.slobodni or 0,
                "ukupno": uk,
                "lat": float(r.lat) if r.lat is not None else None,
                "lon": float(r.lon) if r.lon is not None else None,
            }
        )

    po_sjedistima_rows = db.execute(
        text(
            f"""
            SELECT z.oznaka,
                   z.sjediste,
                   COUNT(m.id) AS ukupno,
                   COUNT(m.id) FILTER (
                     WHERE m.status = 'slobodan'
                       AND (m.rezerviran_do IS NULL OR m.rezerviran_do < NOW())
                   ) AS slobodni,
                   COUNT(m.id) FILTER (WHERE m.status = 'zauzet') AS zauzeti,
                   COUNT(m.id) FILTER (WHERE m.status = 'karantena') AS karantena
            FROM msisdn m
            {OPCINA_JOIN}
            JOIN zupanije z ON z.id = o.zupanija_id
            GROUP BY z.oznaka, z.sjediste
            ORDER BY z.sjediste
            """
        )
    ).fetchall()

    po_sjedistima = []
    for r in po_sjedistima_rows:
        uk = r.ukupno or 0
        zk = (r.zauzeti or 0) + (r.karantena or 0)
        postotak = round((zk / uk) * 100, 2) if uk else 0.0
        po_sjedistima.append(
            {
                "oznaka": r.oznaka,
                "sjediste": r.sjediste,
                "ukupno": uk,
                "slobodni": r.slobodni or 0,
                "zauzeti": r.zauzeti or 0,
                "karantena": r.karantena or 0,
                "postotak_zauzetosti": postotak,
            }
        )

    return {
        "ukupno": ukupno,
        "slobodni": totals.slobodni or 0,
        "zauzeti": zauzeti,
        "karantena": karantena,
        "iskoristivost": iskoristivost,
        "po_opcini": po_opcini,
        "po_sjedistima": po_sjedistima,
    }


def clear_expired_reservations(db: Session) -> int:
    result = db.execute(
        text(
            """
            UPDATE msisdn
            SET rezerviran_do = NULL, updated_at = NOW()
            WHERE rezerviran_do IS NOT NULL AND rezerviran_do < NOW()
            """
        )
    )
    db.commit()
    return result.rowcount


def clear_karantena(db: Session) -> int:
    istekli = db.execute(
        text(
            """
            SELECT id, broj, email, ime, prezime
            FROM msisdn
            WHERE status = 'karantena'
              AND (datum_karantene + (karantena_dana || ' days')::interval) < NOW()
            """
        )
    ).fetchall()

    result = db.execute(
        text(
            """
            UPDATE msisdn
            SET status = 'slobodan',
                datum_karantene = NULL,
                jmbg = NULL,
                ime = NULL,
                prezime = NULL,
                email = NULL,
                adresa = NULL,
                grad = NULL,
                postanski_broj = NULL,
                datum_dodjele = NULL,
                updated_at = NOW()
            WHERE status = 'karantena'
              AND (datum_karantene + (karantena_dana || ' days')::interval) < NOW()
            """
        )
    )
    db.commit()

    from app.services.email_notifications import posalji_email_karantena_end

    for row in istekli:
        posalji_email_karantena_end(
            db, row.id, row.email, row.ime, row.prezime, row.broj
        )

    return result.rowcount
