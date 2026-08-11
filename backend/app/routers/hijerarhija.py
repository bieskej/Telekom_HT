from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin, RequirePregled
from app.database import get_db
from app.schemas import (
    HijerarhijaCvorDetalj,
    HijerarhijaEntitetGroup,
    HijerarhijaOpcinaDetail,
    HijerarhijaPretragaPb,
    HijerarhijaStabloZupanija,
    ImportPostanskiResponse,
)
from app.services import hijerarhija_service
from app.services.postanski_import import import_postanski_uredi

router = APIRouter(tags=["hijerarhija"])


class ImportPostanskiRequest(BaseModel):
    path: str | None = None


@router.post("/admin/import-postanski-uredi", response_model=ImportPostanskiResponse)
async def import_postanski_endpoint(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    body: ImportPostanskiRequest | None = None,
):
    path = Path(body.path) if body and body.path else None
    result = import_postanski_uredi(db, path)
    return ImportPostanskiResponse(**result)


@router.get("/hijerarhija/tree", response_model=list[HijerarhijaEntitetGroup])
async def hijerarhija_tree(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    rows = hijerarhija_service.hijerarhija_tree(db)
    return [HijerarhijaEntitetGroup(**r) for r in rows]


@router.get("/hijerarhija/opcina/{opcina_id}", response_model=HijerarhijaOpcinaDetail)
async def hijerarhija_opcina(
    opcina_id: int,
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    detail = hijerarhija_service.hijerarhija_opcina_detail(db, opcina_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Općina nije pronađena.")
    return HijerarhijaOpcinaDetail(**detail)


@router.get("/hijerarhija/stablo", response_model=list[HijerarhijaStabloZupanija])
async def hijerarhija_stablo(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    """Kompletno stablo Županija → Općina → Lokacija → MSAN sa MSISDN
    brojanjem na svakoj razini. Za master-detail prikaz `/hijerarhija`."""
    return hijerarhija_service.hijerarhija_stablo(db)


@router.get("/hijerarhija/cvor", response_model=HijerarhijaCvorDetalj)
async def hijerarhija_cvor(
    _radnik: RequirePregled,
    tip: str = Query(..., pattern="^(zupanija|opcina|lokacija|uredjaj)$"),
    id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """Detalj jednog čvora: metrike + 10 MSISDN uzoraka + filter za /brojevi."""
    detalj = hijerarhija_service.hijerarhija_cvor_detalj(db, tip, id)
    if not detalj:
        raise HTTPException(status_code=404, detail=f"Čvor {tip}/{id} nije pronađen.")
    return detalj


@router.get("/hijerarhija/pretraga", response_model=HijerarhijaPretragaPb)
async def hijerarhija_pretraga(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
    pb: str = Query(..., min_length=4, max_length=10),
):
    hit = hijerarhija_service.hijerarhija_pretraga_pb(db, pb)
    if not hit:
        raise HTTPException(status_code=404, detail=f"Poštanski broj {pb} nije u sustavu.")
    return HijerarhijaPretragaPb(**hit)
