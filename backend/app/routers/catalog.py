from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled
from app.database import get_db
from app.schemas import KorisnikItem, MsanUredjajItem, OpcinaLokacijeGroup
from app.services import catalog_service

router = APIRouter(tags=["catalog"])


@router.get("/korisnici", response_model=list[KorisnikItem])
async def lista_korisnika(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    rows = catalog_service.lista_korisnika(db)
    return [KorisnikItem(**r) for r in rows]


@router.get("/lokacije-hijerarhija", response_model=list[OpcinaLokacijeGroup])
async def lokacije_hijerarhija(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    rows = catalog_service.lokacije_hijerarhija(db)
    return [OpcinaLokacijeGroup(**r) for r in rows]


@router.get("/msan-uredjaji", response_model=list[MsanUredjajItem])
async def msan_uredjaji(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    rows = catalog_service.lista_msan_uredjaja(db)
    return [MsanUredjajItem(**r) for r in rows]
