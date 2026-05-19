from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled, RequireProdajaIliAdmin
from app.database import get_db
from app.schemas import PortabilnostCreate, PortabilnostItem, PortabilnostPatch
from app.services import portabilnost_service

router = APIRouter(prefix="/portabilnost", tags=["portabilnost"])


@router.get("", response_model=list[PortabilnostItem])
async def lista(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
    tip: str | None = Query(None),
):
    return portabilnost_service.lista_portabilnosti(db, tip)


@router.post("", response_model=PortabilnostItem)
async def kreiraj(
    payload: PortabilnostCreate,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    return portabilnost_service.kreiraj_portabilnost(db, payload.model_dump(), radnik.id)


@router.patch("/{port_id}", response_model=PortabilnostItem)
async def azuriraj(
    port_id: int,
    payload: PortabilnostPatch,
    _radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    return portabilnost_service.azuriraj_portabilnost(
        db, port_id, payload.model_dump(exclude_unset=True)
    )
