from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin
from app.database import get_db
from app.schemas import EmailLogItem, EmailLogListResponse, EmailResendResponse
from app.services.email_notifications import ponovi_email_iz_loga

router = APIRouter(prefix="/admin", tags=["admin-email"])


@router.get("/email-log", response_model=EmailLogListResponse)
async def lista_email_logova(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    msisdn_id: int | None = Query(None),
):
    params: dict = {"limit": limit, "offset": offset}
    where = ["1=1"]
    if status:
        where.append("status = :status")
        params["status"] = status
    if msisdn_id is not None:
        where.append("msisdn_id = :msisdn_id")
        params["msisdn_id"] = msisdn_id
    where_sql = " AND ".join(where)

    ukupno = db.execute(
        text(f"SELECT COUNT(*)::int FROM email_log WHERE {where_sql}"),
        params,
    ).scalar() or 0

    rows = db.execute(
        text(
            f"""
            SELECT id, msisdn_id, primatelj, predmet, status, error_text,
                   sent_at, (html_tijelo IS NOT NULL) AS ima_html
            FROM email_log
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).fetchall()

    return EmailLogListResponse(
        ukupno=ukupno,
        limit=limit,
        offset=offset,
        stavke=[
            EmailLogItem(
                id=r.id,
                msisdn_id=r.msisdn_id,
                primatelj=r.primatelj,
                predmet=r.predmet,
                status=r.status,
                error_text=r.error_text,
                sent_at=r.sent_at,
                ima_html=bool(r.ima_html),
            )
            for r in rows
        ],
    )


@router.get("/email-log/{log_id}/html")
async def email_log_html(
    log_id: int,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT html_tijelo FROM email_log WHERE id = :id"),
        {"id": log_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Log nije pronađen.")
    if not row.html_tijelo:
        raise HTTPException(status_code=404, detail="Log nema HTML sadržaja.")
    return {"html": row.html_tijelo}


@router.post("/email-resend/{log_id}", response_model=EmailResendResponse)
async def email_resend(
    log_id: int,
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
):
    ok, err, new_log_id = ponovi_email_iz_loga(db, log_id)
    if err == "Log nije pronađen.":
        raise HTTPException(status_code=404, detail=err)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "Slanje nije uspjelo.")
    return EmailResendResponse(
        poruka="Email je ponovno poslan.",
        novi_log_id=new_log_id,
    )
