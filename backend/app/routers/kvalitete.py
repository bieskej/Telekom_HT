from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import RequirePregled, get_current_radnik
from app.database import get_db
from app.models import Kvaliteta, Radnik
from app.schemas import KvalitetaResponse

router = APIRouter(tags=["kvaliteta"])


@router.get("/kvalitete", response_model=list[KvalitetaResponse])
async def lista_kvaliteta(
    db: Session = Depends(get_db),
    radnik: Radnik = Depends(get_current_radnik),
):
    rows = db.execute(select(Kvaliteta).order_by(Kvaliteta.cijena)).scalars().all()
    result = []
    for k in rows:
        item = KvalitetaResponse.model_validate(k)
        if k.naziv == "diamond" and radnik.uloga != "admin":
            continue
        result.append(item)
    return result
