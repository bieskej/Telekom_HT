from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Msisdn, Portabilnost

VALID_STATUS = {"zahtjev", "u_obradi", "realiziran", "odbijen"}
VALID_TIP = {"port_in", "port_out"}
PRELAZI = {
    "zahtjev": {"u_obradi", "odbijen"},
    "u_obradi": {"realiziran", "odbijen"},
    "realiziran": set(),
    "odbijen": set(),
}


def _provjeri_prelaz(stari: str, novi: str) -> None:
    if novi not in VALID_STATUS:
        raise HTTPException(status_code=400, detail=f"Nepoznat status: {novi}")
    if novi not in PRELAZI.get(stari, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Prelaz {stari} → {novi} nije dozvoljen.",
        )


def lista_portabilnosti(db: Session, tip: str | None = None) -> list[dict]:
    where = "1=1"
    params: dict = {}
    if tip:
        where += " AND tip = :tip"
        params["tip"] = tip
    rows = db.execute(
        text(
            f"""
            SELECT id, msisdn_id, broj, tip, izvor_op, ciljni_op, datum_zahtjeva,
                   datum_realizacije, status, napomena, created_by
            FROM portabilnost
            WHERE {where}
            ORDER BY id DESC
            """
        ),
        params,
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def kreiraj_portabilnost(db: Session, data: dict, radnik_id: int) -> dict:
    tip = data["tip"]
    if tip not in VALID_TIP:
        raise HTTPException(status_code=400, detail="tip mora biti port_in ili port_out")
    p = Portabilnost(
        msisdn_id=data.get("msisdn_id"),
        broj=data.get("broj"),
        tip=tip,
        izvor_op=data["izvor_op"],
        ciljni_op=data["ciljni_op"],
        napomena=data.get("napomena"),
        status="zahtjev",
        created_by=radnik_id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _row_dict(p)


def _row_dict(p: Portabilnost) -> dict:
    return {
        "id": p.id,
        "msisdn_id": p.msisdn_id,
        "broj": p.broj,
        "tip": p.tip,
        "izvor_op": p.izvor_op,
        "ciljni_op": p.ciljni_op,
        "datum_zahtjeva": p.datum_zahtjeva,
        "datum_realizacije": p.datum_realizacije,
        "status": p.status,
        "napomena": p.napomena,
        "created_by": p.created_by,
    }


def azuriraj_portabilnost(db: Session, port_id: int, data: dict) -> dict:
    p = db.get(Portabilnost, port_id)
    if not p:
        raise HTTPException(status_code=404, detail="Zahtjev nije pronađen.")
    if "status" in data and data["status"]:
        _provjeri_prelaz(p.status, data["status"])
        novi = data["status"]
        p.status = novi
        if novi == "realiziran":
            p.datum_realizacije = datetime.now(timezone.utc)
            _realiziraj(db, p)
    if "napomena" in data:
        p.napomena = data["napomena"]
    db.commit()
    db.refresh(p)
    return _row_dict(p)


def _realiziraj(db: Session, p: Portabilnost) -> None:
    if p.tip == "port_out":
        if not p.msisdn_id:
            raise HTTPException(status_code=400, detail="port_out zahtijeva msisdn_id.")
        msisdn = db.get(Msisdn, p.msisdn_id)
        if not msisdn:
            raise HTTPException(status_code=404, detail="MSISDN nije pronađen.")
        msisdn.status = "portano"
        msisdn.updated_at = datetime.now(timezone.utc)
    elif p.tip == "port_in":
        if not p.broj:
            raise HTTPException(status_code=400, detail="port_in zahtijeva broj.")
        postoji = db.execute(
            text("SELECT id FROM msisdn WHERE broj = :broj"),
            {"broj": p.broj},
        ).fetchone()
        if postoji:
            p.msisdn_id = postoji.id
            return
        raspon = db.execute(text("SELECT id FROM rasponi ORDER BY id LIMIT 1")).fetchone()
        if not raspon:
            raise HTTPException(status_code=500, detail="Nema raspona za novi MSISDN.")
        silver_id = db.execute(text("SELECT id FROM kvaliteta WHERE naziv = 'silver' LIMIT 1")).scalar()
        novi = Msisdn(
            broj=p.broj,
            status="zauzet",
            raspon_id=raspon.id,
            kvaliteta_id=silver_id,
        )
        db.add(novi)
        db.flush()
        p.msisdn_id = novi.id
