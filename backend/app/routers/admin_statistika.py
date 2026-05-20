from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin
from app.database import get_db
from app.schemas import DodjeleHeatmapResponse

router = APIRouter(prefix="/admin/statistika", tags=["admin-statistika"])


@router.get("/dodjele-heatmap", response_model=DodjeleHeatmapResponse)
async def dodjele_heatmap(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    dana: int = Query(90, ge=7, le=365),
):
    od = datetime.now(timezone.utc) - timedelta(days=dana)
    rows = db.execute(
        text(
            """
            SELECT EXTRACT(DOW FROM promijenjeno_at)::int AS dow,
                   EXTRACT(HOUR FROM promijenjeno_at)::int AS hour,
                   COUNT(*)::int AS broj
            FROM msisdn_history
            WHERE akcija = 'dodjela' AND promijenjeno_at >= :od
            GROUP BY dow, hour
            """
        ),
        {"od": od},
    ).fetchall()
    celije = [{"dow": r.dow, "hour": r.hour, "broj": r.broj} for r in rows]
    return DodjeleHeatmapResponse(dana=dana, celije=celije)
