export interface Radnik {
  id: number
  email: string
  ime: string
  prezime: string
  uloga: string
  aktivan: boolean
  jmbg?: string | null
}

export interface KupacMsisdnItem {
  id: number
  broj: string
  status: string
  kvaliteta: string | null
  datum_dodjele: string | null
}

export interface KupacMojiBrojeviResponse {
  ukupno: number
  stranica: number
  velicina_stranice: number
  brojevi: KupacMsisdnItem[]
}

export interface PrijavaResponse {
  access_token: string
  token_type: string
  expires_in: number
  radnik: Radnik
}

export interface Statistike {
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
  iskoristivost: number
  po_opcini: OpcinaStatistika[]
  po_sjedistima: SjedisteStatistika[]
}

export interface OpcinaStatistika {
  naziv: string
  postotak_zauzetosti: number
  slobodni: number
  ukupno: number
  lat?: number | null
  lon?: number | null
}

export interface SjedisteStatistika {
  oznaka: string
  sjediste: string
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
  postotak_zauzetosti: number
}

export interface OpcinaGeoFeature {
  type: 'Feature'
  geometry: {
    type: 'Polygon'
    coordinates: number[][][]
  }
  properties: {
    naziv: string
    ukupno: number
    slobodni: number
    postotak_zauzetosti: number
    lat: number
    lon: number
  }
}

export interface OpcineGeoJson {
  type: 'FeatureCollection'
  features: OpcinaGeoFeature[]
}

export interface DodjeleHeatmapCelija {
  dow: number
  hour: number
  broj: number
}

export interface DodjeleHeatmapResponse {
  dana: number
  celije: DodjeleHeatmapCelija[]
}

export interface AuditLogItem {
  id: number
  radnik_id?: number | null
  radnik_email?: string | null
  akcija: string
  entitet: string
  entitet_id?: number | null
  detalji_json?: string | null
  ip?: string | null
  user_agent?: string | null
  created_at?: string | null
}

export interface AuditLogListResponse {
  ukupno: number
  limit: number
  offset: number
  stavke: AuditLogItem[]
}

export interface PortabilnostItem {
  id: number
  msisdn_id?: number | null
  broj?: string | null
  tip: string
  izvor_op: string
  ciljni_op: string
  datum_zahtjeva?: string | null
  datum_realizacije?: string | null
  status: string
  napomena?: string | null
  created_by?: number | null
}

export interface ServisniNalogItem {
  id: number
  uredjaj_id: number
  opis: string
  status: 'otvoren' | 'u_obradi' | 'rijesen'
  prioritet: string
  prijavio_id?: number | null
  rijesio_id?: number | null
  created_at?: string | null
  rijeseno_at?: string | null
}

export interface WildcardMsisdnItem {
  id: number
  broj: string
  broj_formatiran: string
  kvaliteta: string
  cijena: number
  opcina_naziv?: string | null
}

export interface WildcardPretragaResponse {
  uzorak: string
  ukupno: number
  rezultati: WildcardMsisdnItem[]
}

export interface KarantenaPatchResponse {
  msisdn_id: number
  karantena_dana: number
  datum_karantene?: string | null
  datum_isteka?: string | null
  karantena_razlog?: string | null
}

export interface MsisdnDetalj {
  id: number
  broj: string
  broj_formatiran: string
  status: string
  datum_karantene?: string | null
  karantena_dana?: number | null
  karantena_razlog?: string | null
  datum_isteka?: string | null
  jmbg?: string | null
  ime?: string | null
  prezime?: string | null
  email?: string | null
  datum_dodjele?: string | null
  kvaliteta_id?: number | null
  kvaliteta?: string | null
  cijena?: number | null
  opcina_naziv?: string | null
}

export interface MsisdnItem {
  id: number
  broj: string
  broj_formatiran: string
  status: string
  opcina_id: number | null
  opcina_naziv: string | null
  uredjaj_id: number | null
  jmbg: string | null
  kvaliteta: string | null
  kvaliteta_naziv?: string | null
  ime: string | null
  prezime: string | null
  email: string | null
}

export interface PlacanjePodaci {
  nacin: 'gotovina' | 'kartica'
  broj_kartice?: string
  datum_isteka?: string
  cvv?: string
  ime_vlasnika?: string
}

export interface PretragaResponse {
  ukupno: number
  stranica: number
  po_stranici: number
  rezultati: MsisdnItem[]
}

export interface Opcina {
  id: number
  naziv: string
  entitet: string
  broj_msisdn?: number | null
}

export interface KorisnikItem {
  ime: string
  prezime: string
  jmbg: string
  email: string | null
  broj_brojeva: number
  broj_zauzet: number
  broj_karantena: number
}

export interface LokacijaHijerarhijaItem {
  id: number
  naziv: string
  postanski_broj: string | null
}

export interface OpcinaLokacijeGroup {
  opcina_naziv: string
  lokacije: LokacijaHijerarhijaItem[]
}

export interface MsanUredjajItem {
  id: number
  naziv: string
  opcina_naziv: string
  kapacitet: number
}

export interface KvalitetaItem {
  id: number
  naziv: string
  cijena: number
}

export interface DodijeliResponse {
  msisdn_id: number
  broj: string
  broj_formatiran: string
  status: string
  kvaliteta: string
  cijena: number
  email_poslan?: boolean
  racun_url: string
  ugovor_url: string
  placanje_status?: string | null
}

export interface PortalKorisnikInfo {
  ime: string
  prezime: string
  email: string
}

export interface ProvjeriJmbgResponse {
  valid: boolean
  jmbg: string
  postojeci_brojevi: number
  prethodno_ime: string | null
  prethodno_prezime: string | null
  portal_korisnik: PortalKorisnikInfo | null
  upozorenja: string[]
}

export interface DodijeliBulkStavka {
  msisdn_id: number
  broj_formatiran: string
  racun_url: string
  ugovor_url: string
}

export interface DodijeliBulkResponse {
  dodijeljeno: number
  brojevi: string[]
  brojevi_formatirani: string[]
  msisdn_ids: number[]
  stavke: DodijeliBulkStavka[]
  kvaliteta: string
  cijena_po_komadu: number
  ukupna_cijena: number
  email_poslan?: boolean
  placanje_status?: string | null
}

export interface RezervirajResponse {
  msisdn_id: number
  preostalo_sekundi: number
  broj: string
  broj_formatiran: string
}

export interface ImportRakResponse {
  novi_rasponi: number
  novi_brojevi: number
  preskoceni: number
  obradeno_blokova?: number
  ukupno_pokusano?: number
}

export interface TestEmailResponse {
  poslano: boolean
  poruka: string
  smtp_konfiguriran: boolean
}

export interface ImportPostanskiResponse {
  ukupno: number
  novi: number
  azurirani: number
  preskoceni: number
  needs_review_count: number
  needs_review: Record<string, unknown>[]
  po_operateru: Record<string, number>
}

export interface HijerarhijaOpcinaTreeItem {
  id: number
  naziv: string
  tip_jedinice: string | null
  broj_postanskih: number
  broj_lokacija_ht: number
}

export interface HijerarhijaZupanijaTreeItem {
  id: number
  naziv: string
  oznaka: string
  opcine: HijerarhijaOpcinaTreeItem[]
}

export interface HijerarhijaEntitetGroup {
  entitet: string
  zupanije: HijerarhijaZupanijaTreeItem[]
}

export interface HijerarhijaPretragaPb {
  entitet: string
  zupanija_id: number
  zupanija_naziv: string
  zupanija_oznaka: string
  opcina_id: number
  opcina_naziv: string
  tip_jedinice: string | null
  lokacija_id: number
  lokacija_naziv: string
  postanski_broj: string | null
  posta_operater: string | null
}

export interface HijerarhijaOpcinaDetail {
  opcina: {
    id: number
    naziv: string
    tip_jedinice: string | null
    entitet: string
    zupanija_naziv: string
    zupanija_oznaka: string
  }
  postanski_uredi: {
    id: number
    naziv: string
    postanski_broj: string | null
    posta_operater: string | null
  }[]
  lokacije_ht: {
    id: number
    naziv: string
    tip: string
    uredjaji: {
      id: number
      tip: string
      oznaka: string
      rasponi: {
        id: number
        pocetak: string
        kraj: string
        msisdn_ukupno: number
        zauzet: number
        slobodan: number
      }[]
    }[]
  }[]
}

export interface HijerarhijaStabloUredjaj {
  tip: 'uredjaj'
  id: number
  naziv: string
  uredjaj_tip: string
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
}

export interface HijerarhijaStabloLokacija {
  tip: 'lokacija'
  id: number
  naziv: string
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
  uredjaji: HijerarhijaStabloUredjaj[]
}

export interface HijerarhijaStabloOpcina {
  tip: 'opcina'
  id: number
  naziv: string
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
  lokacije: HijerarhijaStabloLokacija[]
}

export interface HijerarhijaStabloZupanija {
  tip: 'zupanija'
  id: number
  naziv: string
  oznaka: string
  entitet: string
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
  opcine: HijerarhijaStabloOpcina[]
}

export type HijerarhijaCvorTip = 'zupanija' | 'opcina' | 'lokacija' | 'uredjaj'

export interface HijerarhijaCvorBrojUzorak {
  id: number
  broj: string
  status: string
  kvaliteta: string
}

export interface HijerarhijaCvorMetrike {
  ukupno: number
  slobodni: number
  zauzeti: number
  karantena: number
}

export interface HijerarhijaCvorDetalj {
  tip: HijerarhijaCvorTip
  id: number
  naslov: string
  opis: string
  metrike: HijerarhijaCvorMetrike
  brojevi_uzorak: HijerarhijaCvorBrojUzorak[]
  filter_param: { kljuc: string; vrijednost: string } | null
}

export interface EmailLogItem {
  id: number
  msisdn_id?: number | null
  primatelj: string
  predmet: string
  status: string
  error_text?: string | null
  sent_at?: string | null
  ima_html: boolean
}

export interface EmailLogListResponse {
  ukupno: number
  limit: number
  offset: number
  stavke: EmailLogItem[]
}

export interface EmailResendResponse {
  poruka: string
  novi_log_id?: number | null
}
