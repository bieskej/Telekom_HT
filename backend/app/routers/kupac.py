from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireKupac
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models import Radnik
from app.schemas import (
    KupacKontaktRequest,
    KupacMojiBrojeviResponse,
    KupacMsisdnItem,
    KupacRegistracijaRequest,
    PrijavaRequest,
    PrijavaResponse,
    RadnikResponse,
)
from app.services import kupac_service
from app.services.jmbg import validiraj_jmbg

router = APIRouter(prefix="/kupac", tags=["kupac"])


@router.post("/registracija", response_model=RadnikResponse, status_code=status.HTTP_201_CREATED)
async def kupac_registracija(payload: KupacRegistracijaRequest, db: Session = Depends(get_db)):
    try:
        kupac = kupac_service.registracija_kupca(
            db,
            ime=payload.ime,
            prezime=payload.prezime,
            email=payload.email,
            jmbg=payload.jmbg,
            lozinka_hash=hash_password(payload.lozinka),
        )
    except ValueError as e:
        if str(e) == "jmbg_neispravan":
            raise HTTPException(status_code=400, detail="JMBG nije ispravan.") from e
        if str(e) == "email_postoji":
            raise HTTPException(status_code=409, detail="Email je već registriran.") from e
        if str(e) == "jmbg_postoji":
            raise HTTPException(status_code=409, detail="JMBG je već registriran.") from e
        raise
    return RadnikResponse.model_validate(kupac)


@router.post("/prijava", response_model=PrijavaResponse)
async def kupac_prijava(payload: PrijavaRequest, db: Session = Depends(get_db)):
    radnik = db.execute(select(Radnik).where(Radnik.email == payload.email)).scalar_one_or_none()
    if not radnik or not verify_password(payload.lozinka, radnik.lozinka_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravan email ili lozinka.",
        )
    if radnik.uloga != "kupac":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ovaj račun nije kupac. Koristite prijavu za radnike.",
        )
    if not radnik.aktivan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Račun nije aktivan.")
    if not radnik.jmbg:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Račun kupca nema upisan JMBG.",
        )

    token = create_access_token(radnik.id, radnik.email, radnik.uloga)
    expires_in = settings.jwt_expire_hours * 3600
    return PrijavaResponse(
        access_token=token,
        expires_in=expires_in,
        radnik=RadnikResponse.model_validate(radnik),
    )


@router.get("/moji-brojevi", response_model=KupacMojiBrojeviResponse)
async def kupac_moji_brojevi(
    kupac: RequireKupac,
    db: Session = Depends(get_db),
    stranica: int = Query(1, ge=1),
    velicina: int = Query(20, ge=1, le=100),
):
    rez = kupac_service.moji_brojevi(db, kupac.jmbg or "", stranica=stranica, velicina=velicina)
    return KupacMojiBrojeviResponse(
        ukupno=rez["ukupno"],
        stranica=rez["stranica"],
        velicina_stranice=rez["velicina_stranice"],
        brojevi=[KupacMsisdnItem(**b) for b in rez["brojevi"]],
    )


@router.get("/ugovor/{msisdn_id}")
async def kupac_ugovor(
    msisdn_id: int,
    kupac: RequireKupac,
    db: Session = Depends(get_db),
):
    try:
        pdf = kupac_service.preuzmi_ugovor_pdf(db, msisdn_id, kupac.jmbg or "")
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemate pristup ugovoru za ovaj broj.",
        ) from None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ugovor_{msisdn_id}.pdf"'},
    )


@router.post("/kontakt", status_code=status.HTTP_201_CREATED)
async def kupac_kontakt(
    payload: KupacKontaktRequest,
    kupac: RequireKupac,
    db: Session = Depends(get_db),
):
    zapis = kupac_service.posalji_kontakt(db, kupac.id, payload.predmet, payload.poruka)
    kupac_service.opcionalno_posalji_admin_email(kupac, payload.predmet, payload.poruka)
    return {"id": zapis.id, "poruka": "Poruka je zaprimljena."}
