from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled, RequireProdajaIliAdmin
from app.database import get_db
from app.schemas import ServisniNalogCreate, ServisniNalogItem, ServisniNalogPatch
from app.services import servisni_nalog_service

router = APIRouter(prefix="/servisni-nalozi", tags=["servisni-nalozi"])


@router.get("", response_model=list[ServisniNalogItem])
async def lista(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    return servisni_nalog_service.lista_naloga(db)


@router.post("", response_model=ServisniNalogItem)
async def kreiraj(
    payload: ServisniNalogCreate,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    return servisni_nalog_service.kreiraj_nalog(db, payload.model_dump(), radnik.id)


@router.patch("/{nalog_id}", response_model=ServisniNalogItem)
async def azuriraj(
    nalog_id: int,
    payload: ServisniNalogPatch,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    return servisni_nalog_service.azuriraj_nalog(
        db, nalog_id, payload.model_dump(exclude_unset=True), radnik.id
    )
