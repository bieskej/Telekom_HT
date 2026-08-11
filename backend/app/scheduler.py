import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.services.invoice_email import ponovi_neuspjele_emailove
from app.services.iskoristivost_alerts import provjeri_i_posalji_upozorenja_iskoristivost
from app.services.email_notifications import posalji_digest_admin
from app.services.msisdn_service import clear_expired_reservations, clear_karantena

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="Europe/Sarajevo")


def _job_clear_reservations() -> None:
    db = SessionLocal()
    try:
        count = clear_expired_reservations(db)
        if count:
            logger.info("Očišćeno isteklih rezervacija: %s", count)
    finally:
        db.close()


def _job_retry_emails() -> None:
    count = ponovi_neuspjele_emailove()
    if count:
        logger.info("Ponovno poslano emailova: %s", count)


def _job_clear_karantena() -> None:
    db = SessionLocal()
    try:
        count = clear_karantena(db)
        if count:
            logger.info("Oslobođeno iz karantene: %s brojeva", count)
    finally:
        db.close()


def _job_iskoristivost_upozorenja() -> None:
    count = provjeri_i_posalji_upozorenja_iskoristivost()
    if count:
        logger.info("Poslano upozorenja za iskorištenost: %s općina", count)


def _job_digest_admin() -> None:
    db = SessionLocal()
    try:
        if posalji_digest_admin(db):
            logger.info("Tjedni digest admina poslan.")
    except Exception:
        logger.exception("Greška u jobu tjednog digesta")
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_job_clear_reservations, "interval", minutes=1, id="clear_reservations")
    scheduler.add_job(_job_clear_karantena, "cron", hour=0, minute=0, id="clear_karantena")
    scheduler.add_job(_job_retry_emails, "interval", minutes=15, id="retry_emails")
    scheduler.add_job(
        _job_iskoristivost_upozorenja,
        "cron",
        hour=8,
        minute=0,
        id="iskoristivost_upozorenja",
    )
    scheduler.add_job(
        _job_digest_admin,
        "cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        timezone="UTC",
        id="digest_admin",
    )
    scheduler.start()
    logger.info("APScheduler pokrenut.")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
