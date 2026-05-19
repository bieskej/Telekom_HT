from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class PrijavaRequest(BaseModel):
    email: EmailStr
    lozinka: str


class PrijavaResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    radnik: "RadnikResponse"


class RadnikResponse(BaseModel):
    id: int
    email: str
    ime: str
    prezime: str
    uloga: str
    aktivan: bool
    jmbg: str | None = None

    model_config = {"from_attributes": True}


class RadnikCreateRequest(BaseModel):
    email: EmailStr
    ime: str
    prezime: str
    lozinka: str = Field(min_length=4)
    # kupac: portal (email+lozinka+jmbg); ostalo: interni radnici
    uloga: str = Field(pattern="^(admin|prodaja|promet|kupac)$")
    aktivan: bool = True
    jmbg: str | None = Field(default=None, min_length=13, max_length=13)


class RadnikUpdateRequest(BaseModel):
    email: EmailStr | None = None
    ime: str | None = None
    prezime: str | None = None
    lozinka: str | None = Field(default=None, min_length=4)
    uloga: str | None = Field(default=None, pattern="^(admin|prodaja|promet|kupac)$")
    aktivan: bool | None = None
    jmbg: str | None = Field(default=None, min_length=13, max_length=13)


class KupacRegistracijaRequest(BaseModel):
    ime: str = Field(min_length=1, max_length=100)
    prezime: str = Field(min_length=1, max_length=100)
    email: EmailStr
    jmbg: str = Field(min_length=13, max_length=13)
    lozinka: str = Field(min_length=4)


class KupacKontaktRequest(BaseModel):
    predmet: str = Field(min_length=1, max_length=255)
    poruka: str = Field(min_length=1, max_length=5000)


class KupacMsisdnItem(BaseModel):
    id: int
    broj: str
    status: str
    kvaliteta: str | None = None
    datum_dodjele: datetime | None = None


class KupacMojiBrojeviResponse(BaseModel):
    ukupno: int
    stranica: int
    velicina_stranice: int
    brojevi: list[KupacMsisdnItem]


class OpcinaResponse(BaseModel):
    id: int
    naziv: str
    entitet: str
    broj_msisdn: int | None = None

    model_config = {"from_attributes": True}


class KvalitetaResponse(BaseModel):
    id: int
    naziv: str
    cijena: float

    model_config = {"from_attributes": True}


class PlacanjePodaciRequest(BaseModel):
    nacin: Literal["gotovina", "kartica"] = "gotovina"
    broj_kartice: str | None = None
    datum_isteka: str | None = None
    cvv: str | None = None
    ime_vlasnika: str | None = None

    @model_validator(mode="after")
    def provjeri_karticu(self):
        if self.nacin == "kartica":
            if not self.broj_kartice or not self.datum_isteka or not self.cvv or not self.ime_vlasnika:
                raise ValueError("Za plaćanje karticom sva polja kartice su obavezna.")
        return self


class DodijeliBrojRequest(BaseModel):
    opcina_naziv: str
    ime: str
    prezime: str
    jmbg: str = Field(min_length=13, max_length=13)
    email: EmailStr
    adresa: str = Field(min_length=3)
    grad: str = Field(min_length=2, max_length=100)
    postanski_broj: str = Field(min_length=4, max_length=10)
    msisdn_id: int | None = None
    kvaliteta_id: int | None = None
    placanje: PlacanjePodaciRequest = Field(default_factory=PlacanjePodaciRequest)


class DodijeliBrojResponse(BaseModel):
    msisdn_id: int
    broj: str
    broj_formatiran: str
    status: str
    kvaliteta: str
    cijena: float
    email_poslan: bool = False
    racun_url: str
    ugovor_url: str
    placanje_status: str | None = None


class OslobodiRequest(BaseModel):
    karantena_dana: int | None = None


class OslobodiResponse(BaseModel):
    poruka: str
    msisdn_id: int
    status: str
    karantena_dana: int


class KarantenaPatchRequest(BaseModel):
    produzi_dana: int | None = Field(None, ge=1, le=180)
    skrati_dana: int | None = Field(None, ge=1, le=180)
    razlog: str | None = Field(None, max_length=255)


class KarantenaPatchResponse(BaseModel):
    msisdn_id: int
    karantena_dana: int
    datum_karantene: datetime | None = None
    datum_isteka: datetime | None = None
    karantena_razlog: str | None = None


class MsisdnOslobodiKarantenaRequest(BaseModel):
    razlog: str | None = Field(None, max_length=255)


class MsisdnOslobodiKarantenaResponse(BaseModel):
    poruka: str
    msisdn_id: int
    status: str


class PortabilnostCreate(BaseModel):
    tip: str
    izvor_op: str
    ciljni_op: str
    msisdn_id: int | None = None
    broj: str | None = None
    napomena: str | None = None


class PortabilnostPatch(BaseModel):
    status: str | None = None
    napomena: str | None = None


class PortabilnostItem(BaseModel):
    id: int
    msisdn_id: int | None = None
    broj: str | None = None
    tip: str
    izvor_op: str
    ciljni_op: str
    datum_zahtjeva: datetime | None = None
    datum_realizacije: datetime | None = None
    status: str
    napomena: str | None = None
    created_by: int | None = None


class ServisniNalogCreate(BaseModel):
    uredjaj_id: int
    opis: str
    prioritet: str = "srednji"


class ServisniNalogPatch(BaseModel):
    status: str | None = None
    prioritet: str | None = None
    opis: str | None = None


class ServisniNalogItem(BaseModel):
    id: int
    uredjaj_id: int
    opis: str
    status: str
    prioritet: str
    prijavio_id: int | None = None
    rijesio_id: int | None = None
    created_at: datetime | None = None
    rijeseno_at: datetime | None = None


class WildcardMsisdnItem(BaseModel):
    id: int
    broj: str
    broj_formatiran: str
    kvaliteta: str
    cijena: float
    opcina_naziv: str | None = None


class WildcardPretragaResponse(BaseModel):
    uzorak: str
    ukupno: int
    rezultati: list[WildcardMsisdnItem] = Field(default_factory=list)


class MsisdnDetaljResponse(BaseModel):
    id: int
    broj: str
    broj_formatiran: str
    status: str
    datum_karantene: datetime | None = None
    karantena_dana: int | None = None
    karantena_razlog: str | None = None
    datum_isteka: datetime | None = None
    jmbg: str | None = None
    ime: str | None = None
    prezime: str | None = None
    email: str | None = None
    datum_dodjele: datetime | None = None
    kvaliteta_id: int | None = None
    kvaliteta: str | None = None
    cijena: float | None = None
    opcina_naziv: str | None = None


class RezervirajSljedeciRequest(BaseModel):
    opcina_naziv: str
    kvaliteta_id: int | None = None
    kvaliteta_naziv: str | None = Field(
        default=None,
        pattern="^(silver|gold|platinum|diamond)$",
    )


class RezervirajResponse(BaseModel):
    msisdn_id: int
    preostalo_sekundi: int
    broj: str
    broj_formatiran: str


class DodijeliBulkRequest(BaseModel):
    opcina_naziv: str
    broj_brojeva: int = Field(ge=1, le=100)
    korisnik_ime: str
    korisnik_prezime: str
    korisnik_jmbg: str = Field(min_length=13, max_length=13)
    korisnik_email: EmailStr
    adresa: str = Field(min_length=3)
    grad: str = Field(min_length=2, max_length=100)
    postanski_broj: str = Field(min_length=4, max_length=10)
    kvaliteta_naziv: str = Field(default="silver", pattern="^(silver|gold|platinum|diamond)$")
    placanje: PlacanjePodaciRequest = Field(default_factory=PlacanjePodaciRequest)


class DodijeliBulkStavkaResponse(BaseModel):
    msisdn_id: int
    broj_formatiran: str
    racun_url: str
    ugovor_url: str


class DodijeliBulkResponse(BaseModel):
    dodijeljeno: int
    brojevi: list[str]
    brojevi_formatirani: list[str]
    msisdn_ids: list[int]
    stavke: list[DodijeliBulkStavkaResponse]
    kvaliteta: str
    cijena_po_komadu: float
    ukupna_cijena: float
    email_poslan: bool = False
    placanje_status: str | None = None


class ImportRakResponse(BaseModel):
    novi_rasponi: int
    novi_brojevi: int
    preskoceni: int
    obradeno_blokova: int = 0
    ukupno_pokusano: int = 0


class MsisdnPretragaItem(BaseModel):
    id: int
    broj: str
    broj_formatiran: str
    status: str
    opcina_id: int | None = None
    opcina_naziv: str | None = None
    uredjaj_id: int | None = None
    jmbg: str | None = None
    kvaliteta: str | None = None
    kvaliteta_naziv: str | None = None
    ime: str | None = None
    prezime: str | None = None
    email: str | None = None


class MsisdnPretragaResponse(BaseModel):
    ukupno: int
    stranica: int
    po_stranici: int
    rezultati: list[MsisdnPretragaItem]


class OpcinaStatistika(BaseModel):
    naziv: str
    postotak_zauzetosti: float
    slobodni: int
    ukupno: int
    lat: float | None = None
    lon: float | None = None


class SjedisteStatistika(BaseModel):
    oznaka: str
    sjediste: str
    ukupno: int
    slobodni: int
    zauzeti: int
    karantena: int
    postotak_zauzetosti: float


class StatistikeResponse(BaseModel):
    ukupno: int
    slobodni: int
    zauzeti: int
    karantena: int
    iskoristivost: float
    po_opcini: list[OpcinaStatistika]
    po_sjedistima: list[SjedisteStatistika] = Field(default_factory=list)


class KorisnikItem(BaseModel):
    ime: str
    prezime: str
    jmbg: str
    email: str | None = None
    broj_brojeva: int


class LokacijaHijerarhijaItem(BaseModel):
    id: int
    naziv: str
    postanski_broj: str | None = None


class OpcinaLokacijeGroup(BaseModel):
    opcina_naziv: str
    lokacije: list[LokacijaHijerarhijaItem]


class MsanUredjajItem(BaseModel):
    id: int
    naziv: str
    opcina_naziv: str
    kapacitet: int


class ImportPostanskiResponse(BaseModel):
    ukupno: int
    novi: int
    azurirani: int
    preskoceni: int
    needs_review_count: int = 0
    needs_review: list[dict] = Field(default_factory=list)
    po_operateru: dict[str, int] = Field(default_factory=dict)


class HijerarhijaOpcinaTreeItem(BaseModel):
    id: int
    naziv: str
    tip_jedinice: str | None = None
    broj_postanskih: int = 0
    broj_lokacija_ht: int = 0


class HijerarhijaZupanijaTreeItem(BaseModel):
    id: int
    naziv: str
    oznaka: str
    opcine: list[HijerarhijaOpcinaTreeItem] = Field(default_factory=list)


class HijerarhijaEntitetGroup(BaseModel):
    entitet: str
    zupanije: list[HijerarhijaZupanijaTreeItem] = Field(default_factory=list)


class PostanskiUredItem(BaseModel):
    id: int
    naziv: str
    postanski_broj: str | None = None
    posta_operater: str | None = None


class HijerarhijaRasponItem(BaseModel):
    id: int
    pocetak: str
    kraj: str
    msisdn_ukupno: int = 0
    zauzet: int = 0
    slobodan: int = 0


class HijerarhijaUredjajItem(BaseModel):
    id: int
    tip: str
    oznaka: str
    rasponi: list[HijerarhijaRasponItem] = Field(default_factory=list)


class HijerarhijaLokacijaHtItem(BaseModel):
    id: int
    naziv: str
    tip: str
    uredjaji: list[HijerarhijaUredjajItem] = Field(default_factory=list)


class HijerarhijaOpcinaInfo(BaseModel):
    id: int
    naziv: str
    tip_jedinice: str | None = None
    entitet: str
    zupanija_naziv: str
    zupanija_oznaka: str


class HijerarhijaOpcinaDetail(BaseModel):
    opcina: HijerarhijaOpcinaInfo
    postanski_uredi: list[PostanskiUredItem] = Field(default_factory=list)
    lokacije_ht: list[HijerarhijaLokacijaHtItem] = Field(default_factory=list)


class HijerarhijaStabloUredjaj(BaseModel):
    tip: Literal["uredjaj"] = "uredjaj"
    id: int
    naziv: str
    uredjaj_tip: str
    ukupno: int = 0
    slobodni: int = 0
    zauzeti: int = 0
    karantena: int = 0


class HijerarhijaStabloLokacija(BaseModel):
    tip: Literal["lokacija"] = "lokacija"
    id: int
    naziv: str
    ukupno: int = 0
    slobodni: int = 0
    zauzeti: int = 0
    karantena: int = 0
    uredjaji: list[HijerarhijaStabloUredjaj] = Field(default_factory=list)


class HijerarhijaStabloOpcina(BaseModel):
    tip: Literal["opcina"] = "opcina"
    id: int
    naziv: str
    ukupno: int = 0
    slobodni: int = 0
    zauzeti: int = 0
    karantena: int = 0
    lokacije: list[HijerarhijaStabloLokacija] = Field(default_factory=list)


class HijerarhijaStabloZupanija(BaseModel):
    tip: Literal["zupanija"] = "zupanija"
    id: int
    naziv: str
    oznaka: str
    entitet: str
    ukupno: int = 0
    slobodni: int = 0
    zauzeti: int = 0
    karantena: int = 0
    opcine: list[HijerarhijaStabloOpcina] = Field(default_factory=list)


class HijerarhijaCvorBrojUzorak(BaseModel):
    id: int
    broj: str
    status: str
    kvaliteta: str


class HijerarhijaCvorMetrike(BaseModel):
    ukupno: int = 0
    slobodni: int = 0
    zauzeti: int = 0
    karantena: int = 0


class HijerarhijaCvorFilterParam(BaseModel):
    kljuc: str
    vrijednost: str


class HijerarhijaCvorDetalj(BaseModel):
    tip: str
    id: int
    naslov: str
    opis: str
    metrike: HijerarhijaCvorMetrike
    brojevi_uzorak: list[HijerarhijaCvorBrojUzorak] = Field(default_factory=list)
    filter_param: HijerarhijaCvorFilterParam | None = None


class HijerarhijaPretragaPb(BaseModel):
    entitet: str
    zupanija_id: int
    zupanija_naziv: str
    zupanija_oznaka: str
    opcina_id: int
    opcina_naziv: str
    tip_jedinice: str | None = None
    lokacija_id: int
    lokacija_naziv: str
    postanski_broj: str | None = None
    posta_operater: str | None = None


class EmailLogItem(BaseModel):
    id: int
    msisdn_id: int | None = None
    primatelj: str
    predmet: str
    status: str
    error_text: str | None = None
    sent_at: datetime | None = None
    ima_html: bool = False


class EmailLogListResponse(BaseModel):
    ukupno: int
    limit: int
    offset: int
    stavke: list[EmailLogItem] = Field(default_factory=list)


class EmailResendResponse(BaseModel):
    poruka: str
    novi_log_id: int | None = None
