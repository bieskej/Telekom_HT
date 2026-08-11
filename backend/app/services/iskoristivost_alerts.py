import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.email_service import notifikacija_status_poslije_slanja, smtp_configured
from app.services.email_notifications import posalji_iskoristivost_alert
from app.services.msisdn_service import statistike

logger = logging.getLogger(__name__)

PREDMET_UPOZORENJE = "Upozorenje: visoka iskorištenost brojeva - HT Eronet"
TIP_NOTIFIKACIJE = "iskoristivost_upozorenje"


def filtriraj_opce_iznad_praga(po_opcini: list[dict], prag: float) -> list[dict]:
    return [o for o in po_opcini if o.get("postotak_zauzetosti", 0) >= prag]


def _zapisi_notifikaciju_upozorenja(
    db: Session,
    email: str,
    opcina_naziv: str,
    postotak: float,
    slobodni: int,
    poslano: bool | None,
) -> None:
    sadrzaj = (
        f"Općina {opcina_naziv}: zauzetost {postotak:.1f}%, "
        f"slobodnih brojeva {slobodni} (prag {settings.iskoristivost_upozorenje_postotak}%)"
    )
    if poslano is None:
        status = "nedostaje_smtp"
    else:
        status = notifikacija_status_poslije_slanja(poslano)
    db.execute(
        text(
            """
            INSERT INTO notifikacije (email_primatelj, predmet, sadrzaj, status, msisdn_id, poslano_at, tip)
            VALUES (:email, :predmet, :sadrzaj, :status, NULL,
                    CASE WHEN :status = 'poslano' THEN NOW() ELSE NULL END, :tip)
            """
        ),
        {
            "email": email,
            "predmet": PREDMET_UPOZORENJE,
            "sadrzaj": sadrzaj,
            "status": status,
            "tip": TIP_NOTIFIKACIJE,
        },
    )


def obradi_upozorenja_za_opcine(db: Session, opce: list[dict], admin_email: str) -> int:
    if not opce:
        return 0
    if smtp_configured():
        posalji_iskoristivost_alert(
            db, admin_email, opce, settings.iskoristivost_upozorenje_postotak
        )
    for op in opce:
        naziv = op["naziv"]
        postotak = float(op["postotak_zauzetosti"])
        slobodni = int(op["slobodni"])
        poslano = True if smtp_configured() else None
        _zapisi_notifikaciju_upozorenja(db, admin_email, naziv, postotak, slobodni, poslano)
        logger.info(
            "Upozorenje iskorištenosti: %s (%.1f%%, %s slobodnih)",
            naziv,
            postotak,
            slobodni,
        )
    db.commit()
    return len(opce)


def _opcine_za_odgovor(opce: list[dict]) -> list[dict]:
    return [
        {
            "naziv": o["naziv"],
            "postotak_zauzetosti": float(o.get("postotak_zauzetosti", 0)),
            "slobodni": int(o.get("slobodni", 0)),
            "ukupno": int(o.get("ukupno", 0)),
        }
        for o in opce
    ]


def provjeri_iskoristivost_alert() -> dict:
    """Provjeri općine iznad praga, pošalji email adminu i vrati sažetak."""
    prag = settings.iskoristivost_upozorenje_postotak
    smtp_ok = smtp_configured()
    db = SessionLocal()
    try:
        stats = statistike(db)
        opce = filtriraj_opce_iznad_praga(stats["po_opcini"], prag)
        if not opce:
            logger.info("Nema općina iznad praga iskorištenosti (%.0f%%).", prag)
            return {
                "poslano_opcina": 0,
                "prag": prag,
                "opce": [],
                "smtp_konfiguriran": smtp_ok,
            }
        count = obradi_upozorenja_za_opcine(db, opce, settings.admin_alert_email)
        return {
            "poslano_opcina": count,
            "prag": prag,
            "opce": _opcine_za_odgovor(opce),
            "smtp_konfiguriran": smtp_ok,
        }
    except Exception:
        logger.exception("Greška u jobu upozorenja iskorištenosti")
        db.rollback()
        return {
            "poslano_opcina": 0,
            "prag": prag,
            "opce": [],
            "smtp_konfiguriran": smtp_ok,
        }
    finally:
        db.close()


def provjeri_i_posalji_upozorenja_iskoristivost() -> int:
    """Dnevna provjera općina s iskorištenošću >= prag; zapis u notifikacije + email adminu."""
    return provjeri_iskoristivost_alert()["poslano_opcina"]
