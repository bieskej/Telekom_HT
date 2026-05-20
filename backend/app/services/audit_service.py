import json
from datetime import datetime

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session


def zapis_audit(
    db: Session,
    *,
    akcija: str,
    entitet: str,
    entitet_id: int | None = None,
    radnik_id: int | None = None,
    detalji: dict | None = None,
    request: Request | None = None,
) -> None:
    ip = None
    ua = None
    if request:
        ip = request.client.host if request.client else None
        ua = (request.headers.get("user-agent") or "")[:500]
    db.execute(
        text(
            """
            INSERT INTO audit_log (radnik_id, akcija, entitet, entitet_id, detalji_json, ip, user_agent)
            VALUES (:radnik_id, :akcija, :entitet, :entitet_id, :detalji, :ip, :ua)
            """
        ),
        {
            "radnik_id": radnik_id,
            "akcija": akcija,
            "entitet": entitet,
            "entitet_id": entitet_id,
            "detalji": json.dumps(detalji, ensure_ascii=False) if detalji else None,
            "ip": ip,
            "ua": ua,
        },
    )


def lista_audit(
    db: Session,
    *,
    radnik_id: int | None = None,
    entitet: str | None = None,
    od: datetime | None = None,
    do: datetime | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}
    if radnik_id is not None:
        where.append("a.radnik_id = :radnik_id")
        params["radnik_id"] = radnik_id
    if entitet:
        where.append("a.entitet = :entitet")
        params["entitet"] = entitet
    if od:
        where.append("a.created_at >= :od")
        params["od"] = od
    if do:
        where.append("a.created_at <= :do")
        params["do"] = do
    if q and q.strip():
        where.append(
            "(a.akcija ILIKE :q OR a.entitet ILIKE :q OR a.detalji_json ILIKE :q OR r.email ILIKE :q)"
        )
        params["q"] = f"%{q.strip()}%"
    where_sql = " AND ".join(where)
    ukupno = db.execute(
        text(
            f"""
            SELECT COUNT(*)::int FROM audit_log a
            LEFT JOIN radnici r ON r.id = a.radnik_id
            WHERE {where_sql}
            """
        ),
        params,
    ).scalar() or 0
    rows = db.execute(
        text(
            f"""
            SELECT a.id, a.radnik_id, r.email AS radnik_email, a.akcija, a.entitet,
                   a.entitet_id, a.detalji_json, a.ip, a.user_agent, a.created_at
            FROM audit_log a
            LEFT JOIN radnici r ON r.id = a.radnik_id
            WHERE {where_sql}
            ORDER BY a.id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).fetchall()
    return [dict(r._mapping) for r in rows], ukupno


def export_csv(db: Session, **filters) -> str:
    stavke, _ = lista_audit(db, limit=10000, offset=0, **filters)
    lines = ["id,radnik_id,radnik_email,akcija,entitet,entitet_id,created_at,ip"]
    for s in stavke:
        lines.append(
            f'{s["id"]},{s.get("radnik_id") or ""},{s.get("radnik_email") or ""},'
            f'"{s["akcija"]}","{s["entitet"]}",{s.get("entitet_id") or ""},'
            f'"{s.get("created_at") or ""}","{s.get("ip") or ""}"'
        )
    return "\n".join(lines)
