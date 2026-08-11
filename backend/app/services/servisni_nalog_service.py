from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ServisniNalog

VALID_STATUS = {"otvoren", "u_obradi", "rijesen"}
VALID_PRIORITET = {"niski", "srednji", "kritican"}
PRELAZI = {
    "otvoren": {"u_obradi", "rijesen"},
    "u_obradi": {"rijesen"},
    "rijesen": set(),
}


def _osvjezi_u_kvaru_uredjaja(db: Session, uredjaj_id: int) -> None:
    kritican = db.execute(
        text(
            """
            SELECT 1 FROM servisni_nalog
            WHERE uredjaj_id = :uid AND status = 'otvoren' AND prioritet = 'kritican'
            LIMIT 1
            """
        ),
        {"uid": uredjaj_id},
    ).fetchone()
    flag = kritican is not None
    db.execute(
        text(
            """
            UPDATE msisdn m
            SET u_kvaru = :flag, updated_at = NOW()
            FROM rasponi r
            WHERE r.id = m.raspon_id AND r.uredjaj_id = :uid
            """
        ),
        {"flag": flag, "uid": uredjaj_id},
    )


def _provjeri_uredjaj_postoji(db: Session, uredjaj_id: int) -> None:
    row = db.execute(
        text("SELECT 1 FROM uredjaji WHERE id = :id"),
        {"id": uredjaj_id},
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=400,
            detail=f"Uređaj s ID {uredjaj_id} ne postoji u sustavu.",
        )


def lista_naloga(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT id, uredjaj_id, opis, status, prioritet, prijavio_id, rijesio_id,
                   created_at, rijeseno_at
            FROM servisni_nalog
            ORDER BY
              CASE prioritet WHEN 'kritican' THEN 0 WHEN 'srednji' THEN 1 ELSE 2 END,
              id DESC
            """
        )
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def kreiraj_nalog(db: Session, data: dict, radnik_id: int) -> dict:
    uredjaj_id = data.get("uredjaj_id")
    if not uredjaj_id or int(uredjaj_id) <= 0:
        raise HTTPException(status_code=400, detail="Uređaj je obavezan.")
    uredjaj_id = int(uredjaj_id)
    opis = (data.get("opis") or "").strip()
    if not opis:
        raise HTTPException(status_code=400, detail="Opis naloga je obavezan.")
    prioritet = data.get("prioritet", "srednji")
    if prioritet not in VALID_PRIORITET:
        raise HTTPException(status_code=400, detail="Neispravan prioritet.")
    _provjeri_uredjaj_postoji(db, uredjaj_id)
    n = ServisniNalog(
        uredjaj_id=uredjaj_id,
        opis=opis,
        status="otvoren",
        prioritet=prioritet,
        prijavio_id=radnik_id,
    )
    try:
        db.add(n)
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Uređaj ili radnik nije valjan (provjeri ID uređaja).",
        ) from exc
    if n.status == "otvoren" and n.prioritet == "kritican":
        _osvjezi_u_kvaru_uredjaja(db, n.uredjaj_id)
    try:
        from app.services.audit_service import zapis_audit

        zapis_audit(
            db,
            akcija="servisni_nalog_otvoren",
            entitet="servisni_nalog",
            entitet_id=n.id,
            radnik_id=radnik_id,
            detalji={"uredjaj_id": n.uredjaj_id, "prioritet": n.prioritet},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Spremanje naloga nije uspjelo (provjeri uređaj i migracije).",
        ) from exc
    db.refresh(n)
    return _row_dict(n)


def _row_dict(n: ServisniNalog) -> dict:
    return {
        "id": n.id,
        "uredjaj_id": n.uredjaj_id,
        "opis": n.opis,
        "status": n.status,
        "prioritet": n.prioritet,
        "prijavio_id": n.prijavio_id,
        "rijesio_id": n.rijesio_id,
        "created_at": n.created_at,
        "rijeseno_at": n.rijeseno_at,
    }


def azuriraj_nalog(db: Session, nalog_id: int, data: dict, radnik_id: int) -> dict:
    n = db.get(ServisniNalog, nalog_id)
    if not n:
        raise HTTPException(status_code=404, detail="Nalog nije pronađen.")
    uredjaj_id = n.uredjaj_id
    if "status" in data and data["status"]:
        novi = data["status"]
        if novi not in VALID_STATUS:
            raise HTTPException(status_code=400, detail="Neispravan status.")
        if novi not in PRELAZI.get(n.status, set()):
            raise HTTPException(status_code=400, detail=f"Prelaz {n.status} → {novi} nije dozvoljen.")
        n.status = novi
        if novi == "rijesen":
            n.rijeseno_at = datetime.now(timezone.utc)
            n.rijesio_id = radnik_id
            from app.services.audit_service import zapis_audit

            zapis_audit(
                db,
                akcija="servisni_nalog_zatvoren",
                entitet="servisni_nalog",
                entitet_id=n.id,
                radnik_id=radnik_id,
                detalji={"uredjaj_id": n.uredjaj_id},
            )
    if "prioritet" in data and data["prioritet"]:
        if data["prioritet"] not in VALID_PRIORITET:
            raise HTTPException(status_code=400, detail="Neispravan prioritet.")
        n.prioritet = data["prioritet"]
    if "opis" in data:
        n.opis = data["opis"]
    db.flush()
    _osvjezi_u_kvaru_uredjaja(db, uredjaj_id)
    db.commit()
    db.refresh(n)
    return _row_dict(n)
