import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Placanje
from app.services.payment_crypto import hash_sensitive

KARTICA_REGEX = re.compile(r"^\d{16}$")
ISTEK_REGEX = re.compile(r"^(0[1-9]|1[0-2])\/\d{2}$")
CVV_REGEX = re.compile(r"^\d{3}$")


def kreiraj_placanje(
    db: Session,
    msisdn_id: int,
    nacin: str,
    iznos: float,
    *,
    broj_kartice: str | None = None,
    datum_isteka: str | None = None,
    cvv: str | None = None,
    ime_vlasnika: str | None = None,
) -> Placanje:
    nacin_norm = nacin.lower().strip()
    if nacin_norm not in ("gotovina", "kartica"):
        raise HTTPException(status_code=400, detail="Način plaćanja mora biti gotovina ili kartica.")

    broj_hash = None
    cvv_hash = None
    istek = None
    vlasnik = None

    if nacin_norm == "kartica":
        if not broj_kartice or not KARTICA_REGEX.match(broj_kartice.replace(" ", "")):
            raise HTTPException(status_code=400, detail="Broj kartice mora imati 16 znamenki.")
        if not datum_isteka or not ISTEK_REGEX.match(datum_isteka.strip()):
            raise HTTPException(status_code=400, detail="Datum isteka mora biti u formatu MM/GG.")
        if not cvv or not CVV_REGEX.match(cvv.strip()):
            raise HTTPException(status_code=400, detail="CVV mora imati 3 znamenke.")
        if not ime_vlasnika or len(ime_vlasnika.strip()) < 2:
            raise HTTPException(status_code=400, detail="Ime vlasnika kartice je obavezno.")

        broj_hash = hash_sensitive(broj_kartice.replace(" ", ""))
        cvv_hash = hash_sensitive(cvv.strip())
        istek = datum_isteka.strip()
        vlasnik = ime_vlasnika.strip()

    placanje = Placanje(
        msisdn_id=msisdn_id,
        nacin=nacin_norm,
        broj_kartice_hash=broj_hash,
        datum_isteka=istek,
        cvv_hash=cvv_hash,
        ime_vlasnika=vlasnik,
        iznos=iznos,
        status="izvrseno",
    )
    db.add(placanje)
    db.flush()
    return placanje
