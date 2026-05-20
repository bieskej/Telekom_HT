from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, verify_password
from app.config import settings
from app.database import get_db
from app.models import Radnik
from app.schemas import PrijavaRequest, PrijavaResponse, RadnikResponse

router = APIRouter(tags=["autentifikacija"])


@router.post("/prijava", response_model=PrijavaResponse)
async def prijava(payload: PrijavaRequest, request: Request, db: Session = Depends(get_db)):
    radnik = db.execute(select(Radnik).where(Radnik.email == payload.email)).scalar_one_or_none()
    if not radnik or not verify_password(payload.lozinka, radnik.lozinka_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravan email ili lozinka.",
        )
    if hasattr(radnik, "aktivan") and radnik.aktivan is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Račun nije aktivan.")
    if radnik.uloga == "kupac":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kupci se prijavljuju putem portala (/kupac/prijava).",
        )

    from app.services.audit_service import zapis_audit

    zapis_audit(
        db,
        akcija="prijava",
        entitet="radnik",
        entitet_id=radnik.id,
        radnik_id=radnik.id,
        detalji={"email": radnik.email, "uloga": radnik.uloga},
        request=request,
    )
    db.commit()

    token = create_access_token(radnik.id, radnik.email, radnik.uloga)
    expires_in = settings.jwt_expire_hours * 3600
    return PrijavaResponse(
        access_token=token,
        expires_in=expires_in,
        radnik=RadnikResponse.model_validate(radnik),
    )
