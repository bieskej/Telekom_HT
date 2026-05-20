from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin
from app.database import get_db
from app.schemas import AuditLogListResponse
from app.services.audit_service import export_csv, lista_audit

router = APIRouter(prefix="/admin", tags=["admin-audit"])


@router.get("/audit-log", response_model=AuditLogListResponse)
async def audit_log_lista(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    radnik_id: int | None = None,
    entitet: str | None = None,
    od: datetime | None = None,
    do: datetime | None = None,
    q: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    stavke, ukupno = lista_audit(
        db,
        radnik_id=radnik_id,
        entitet=entitet,
        od=od,
        do=do,
        q=q,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(ukupno=ukupno, limit=limit, offset=offset, stavke=stavke)


@router.get("/audit-log/export.csv")
async def audit_log_export(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    radnik_id: int | None = None,
    entitet: str | None = None,
    od: datetime | None = None,
    do: datetime | None = None,
    q: str | None = None,
):
    csv_text = export_csv(db, radnik_id=radnik_id, entitet=entitet, od=od, do=do, q=q)
    return PlainTextResponse(csv_text, media_type="text/csv")
