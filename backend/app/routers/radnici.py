from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin
from app.auth.security import hash_password
from app.database import get_db
from app.models import Radnik
from app.services.jmbg import validiraj_jmbg
from app.schemas import RadnikCreateRequest, RadnikResponse, RadnikUpdateRequest

router = APIRouter(prefix="/radnici", tags=["radnici"])


@router.get("", response_model=list[RadnikResponse])
async def lista_radnika(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    """Svi korisnici sustava (uključujući kupce s portala)."""
    rows = db.execute(select(Radnik).order_by(Radnik.uloga, Radnik.prezime, Radnik.ime)).scalars().all()
    return [RadnikResponse.model_validate(r) for r in rows]


@router.post("", response_model=RadnikResponse, status_code=status.HTTP_201_CREATED)
async def kreiraj_radnika(
    payload: RadnikCreateRequest,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    postoji = db.execute(select(Radnik).where(Radnik.email == payload.email)).scalar_one_or_none()
    if postoji:
        raise HTTPException(status_code=400, detail="Email je već u upotrebi.")
    if payload.jmbg and not validiraj_jmbg(payload.jmbg):
        raise HTTPException(status_code=400, detail="JMBG nije ispravan.")
    radnik = Radnik(
        email=payload.email,
        ime=payload.ime,
        prezime=payload.prezime,
        lozinka_hash=hash_password(payload.lozinka),
        uloga=payload.uloga,
        aktivan=payload.aktivan,
        jmbg=payload.jmbg,
    )
    db.add(radnik)
    db.commit()
    db.refresh(radnik)
    return RadnikResponse.model_validate(radnik)


@router.put("/{radnik_id}", response_model=RadnikResponse)
async def azuriraj_radnika(
    radnik_id: int,
    payload: RadnikUpdateRequest,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    radnik = db.get(Radnik, radnik_id)
    if not radnik:
        raise HTTPException(status_code=404, detail="Radnik nije pronađen.")

    data = payload.model_dump(exclude_unset=True)
    if "lozinka" in data:
        data["lozinka_hash"] = hash_password(data.pop("lozinka"))
    if "email" in data and data["email"] != radnik.email:
        postoji = db.execute(select(Radnik).where(Radnik.email == data["email"])).scalar_one_or_none()
        if postoji:
            raise HTTPException(status_code=400, detail="Email je već u upotrebi.")

    for key, value in data.items():
        setattr(radnik, key, value)
    db.commit()
    db.refresh(radnik)
    return RadnikResponse.model_validate(radnik)


@router.delete("/{radnik_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deaktiviraj_radnika(
    radnik_id: int,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    radnik = db.get(Radnik, radnik_id)
    if not radnik:
        raise HTTPException(status_code=404, detail="Radnik nije pronađen.")
    radnik.aktivan = False
    db.commit()
