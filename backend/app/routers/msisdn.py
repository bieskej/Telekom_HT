from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import RequireAdmin, RequirePregled, RequireProdajaIliAdmin
from app.database import get_db
from app.schemas import (
    DodijeliBrojRequest,
    DodijeliBrojResponse,
    DodijeliBulkRequest,
    DodijeliBulkResponse,
    ImportRakResponse,
    KarantenaPatchRequest,
    KarantenaPatchResponse,
    MsisdnDetaljResponse,
    MsisdnOslobodiKarantenaRequest,
    MsisdnOslobodiKarantenaResponse,
    MsisdnPretragaResponse,
    OslobodiRequest,
    OslobodiResponse,
    ProvjeriJmbgResponse,
    RezervirajResponse,
    RezervirajSljedeciRequest,
    StatistikeResponse,
    VratiAktivnoRequest,
    VratiAktivnoResponse,
    WildcardPretragaResponse,
)
from app.services import msisdn_service
from app.services.dokumenti_service import osiguraj_dokumente
from app.services.rak_import import import_rak_datoteka

router = APIRouter(tags=["msisdn"])


@router.post("/dodijeli-broj", response_model=DodijeliBrojResponse)
async def dodijeli_broj(
    payload: DodijeliBrojRequest,
    background_tasks: BackgroundTasks,
    radnik: RequireProdajaIliAdmin,
    request: Request,
    db: Session = Depends(get_db),
):
    result = msisdn_service.dodijeli_broj(
        db,
        payload.opcina_naziv,
        payload.ime,
        payload.prezime,
        payload.jmbg,
        payload.email,
        payload.adresa,
        payload.grad,
        payload.postanski_broj,
        background_tasks,
        payload.msisdn_id,
        payload.kvaliteta_id,
        radnik.uloga,
        placanje=payload.placanje.model_dump(),
    )
    from app.services.audit_service import zapis_audit

    zapis_audit(
        db,
        akcija="dodjela",
        entitet="msisdn",
        entitet_id=result["msisdn_id"],
        radnik_id=radnik.id,
        detalji={"broj": result["broj_formatiran"], "kvaliteta": result["kvaliteta"]},
        request=request,
    )
    db.commit()
    return DodijeliBrojResponse(**result)


@router.get("/msisdn/provjeri-jmbg", response_model=ProvjeriJmbgResponse)
async def provjeri_jmbg_dodjela_endpoint(
    _radnik: RequireProdajaIliAdmin,
    jmbg: str = Query(..., min_length=1),
    ime: str | None = None,
    prezime: str | None = None,
    db: Session = Depends(get_db),
):
    return ProvjeriJmbgResponse(**msisdn_service.provjeri_jmbg_dodjela(db, jmbg, ime, prezime))


@router.post("/oslobodi/{msisdn_id}", response_model=OslobodiResponse)
async def oslobodi(
    msisdn_id: int,
    _radnik: RequireProdajaIliAdmin,
    payload: OslobodiRequest | None = None,
    db: Session = Depends(get_db),
):
    karantena_dana = payload.karantena_dana if payload else None
    result = msisdn_service.oslobodi_broj(db, msisdn_id, karantena_dana)
    return OslobodiResponse(**result)


@router.get("/msisdn/wildcard", response_model=WildcardPretragaResponse)
async def wildcard_pretraga(
    _radnik: RequirePregled,
    uzorak: str = Query(..., min_length=1),
    opcina_naziv: str | None = None,
    kvaliteta_id: int | None = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = msisdn_service.pretrazi_wildcard(db, uzorak, opcina_naziv, kvaliteta_id, limit)
    return WildcardPretragaResponse(**result)


@router.patch("/msisdn/{msisdn_id}/karantena", response_model=KarantenaPatchResponse)
async def patch_karantena(
    msisdn_id: int,
    payload: KarantenaPatchRequest,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    result = msisdn_service.azuriraj_karantenu(
        db,
        msisdn_id,
        produzi_dana=payload.produzi_dana,
        skrati_dana=payload.skrati_dana,
        razlog=payload.razlog,
        radnik_uloga=radnik.uloga,
    )
    return KarantenaPatchResponse(**result)


@router.post("/msisdn/{msisdn_id}/oslobodi", response_model=MsisdnOslobodiKarantenaResponse)
async def oslobodi_iz_karantene(
    msisdn_id: int,
    admin: RequireAdmin,
    request: Request,
    payload: MsisdnOslobodiKarantenaRequest | None = None,
    db: Session = Depends(get_db),
):
    razlog = payload.razlog if payload else None
    result = msisdn_service.oslobodi_iz_karantene_admin(db, msisdn_id, razlog, admin.id)
    from app.services.audit_service import zapis_audit

    zapis_audit(
        db,
        akcija="oslobodeno_iz_karantene",
        entitet="msisdn",
        entitet_id=msisdn_id,
        radnik_id=admin.id,
        detalji={"razlog": razlog},
        request=request,
    )
    db.commit()
    return MsisdnOslobodiKarantenaResponse(**result)


@router.post("/msisdn/{msisdn_id}/vrati-aktivno", response_model=VratiAktivnoResponse)
async def vrati_iz_karantene_u_aktivno(
    msisdn_id: int,
    radnik: RequireProdajaIliAdmin,
    request: Request,
    payload: VratiAktivnoRequest | None = None,
    db: Session = Depends(get_db),
):
    razlog = payload.razlog if payload else None
    result = msisdn_service.vrati_iz_karantene_u_aktivno(db, msisdn_id, razlog, radnik.id)
    from app.services.audit_service import zapis_audit

    zapis_audit(
        db,
        akcija="vraceno_u_aktivno",
        entitet="msisdn",
        entitet_id=msisdn_id,
        radnik_id=radnik.id,
        detalji={"razlog": razlog},
        request=request,
    )
    db.commit()
    return VratiAktivnoResponse(**result)


@router.get("/msisdn/pretraga", response_model=MsisdnPretragaResponse)
async def pretraga_msisdn(
    _radnik: RequirePregled,
    broj: str | None = None,
    status: str | None = None,
    opcina_id: int | None = None,
    opcina_naziv: str | None = None,
    opcina_naziv_tocno: bool = False,
    uredjaj_id: int | None = None,
    lokacija_id: int | None = None,
    korisnik_jmbg: str | None = None,
    korisnik_ime_prezime: str | None = None,
    kvaliteta: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = msisdn_service.pretrazi_msisdn(
        db,
        broj,
        status,
        opcina_id,
        opcina_naziv,
        opcina_naziv_tocno,
        uredjaj_id,
        lokacija_id,
        korisnik_jmbg,
        korisnik_ime_prezime,
        kvaliteta,
        page,
        per_page,
    )
    return MsisdnPretragaResponse(**result)


@router.get("/msisdn/{msisdn_id}", response_model=MsisdnDetaljResponse)
async def msisdn_detalj(
    msisdn_id: int,
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    return MsisdnDetaljResponse(**msisdn_service.dohvati_msisdn_detalj(db, msisdn_id))


@router.post("/rezerviraj-sljedeci", response_model=RezervirajResponse)
async def rezerviraj_sljedeci(
    body: RezervirajSljedeciRequest,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    result = msisdn_service.rezerviraj_sljedeci_opcina(
        db,
        body.opcina_naziv,
        body.kvaliteta_id,
        body.kvaliteta_naziv,
        radnik.uloga,
        exclude_msisdn_id=body.exclude_msisdn_id,
    )
    return RezervirajResponse(**result)


@router.post("/rezerviraj/{msisdn_id}", response_model=RezervirajResponse)
async def rezerviraj(
    msisdn_id: int,
    _radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    result = msisdn_service.rezerviraj_broj(db, msisdn_id)
    return RezervirajResponse(**result)


@router.delete("/rezerviraj/{msisdn_id}")
async def ponisti_rezervaciju(
    msisdn_id: int,
    _radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    return msisdn_service.ponisti_rezervaciju(db, msisdn_id)


@router.post("/dodijeli-bulk", response_model=DodijeliBulkResponse)
async def dodijeli_bulk(
    payload: DodijeliBulkRequest,
    background_tasks: BackgroundTasks,
    radnik: RequireProdajaIliAdmin,
    db: Session = Depends(get_db),
):
    result = msisdn_service.dodijeli_bulk(
        db,
        payload.opcina_naziv,
        payload.broj_brojeva,
        payload.korisnik_ime,
        payload.korisnik_prezime,
        payload.korisnik_jmbg,
        payload.korisnik_email,
        payload.adresa,
        payload.grad,
        payload.postanski_broj,
        payload.kvaliteta_naziv,
        radnik.uloga,
        background_tasks,
        placanje=payload.placanje.model_dump(),
    )
    return DodijeliBulkResponse(**result)


@router.get("/msisdn/{msisdn_id}/racun")
async def preuzmi_racun(
    msisdn_id: int,
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    try:
        pdf = osiguraj_dokumente(db, msisdn_id, "racun")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="racun_{msisdn_id}.pdf"'},
    )


@router.get("/msisdn/{msisdn_id}/ugovor")
async def preuzmi_ugovor(
    msisdn_id: int,
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    try:
        pdf = osiguraj_dokumente(db, msisdn_id, "ugovor")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ugovor_{msisdn_id}.pdf"'},
    )


@router.get("/statistike", response_model=StatistikeResponse)
async def statistike(
    _radnik: RequirePregled,
    db: Session = Depends(get_db),
):
    result = msisdn_service.statistike(db)
    return StatistikeResponse(**result)


@router.post("/admin/import-rak", response_model=ImportRakResponse)
async def import_rak(
    _admin: RequireAdmin,
    db: Session = Depends(get_db),
    datoteka: UploadFile = File(...),
):
    if not datoteka.filename:
        raise HTTPException(status_code=400, detail="Datoteka nije priložena.")
    result = import_rak_datoteka(datoteka.file, datoteka.filename, db)
    return ImportRakResponse(**result)
