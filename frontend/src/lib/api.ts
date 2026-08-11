import type {
  DodijeliBulkResponse,
  DodijeliResponse,
  PlacanjePodaci,
  ImportRakResponse,
  ImportPostanskiResponse,
  HijerarhijaEntitetGroup,
  HijerarhijaOpcinaDetail,
  HijerarhijaPretragaPb,
  KorisnikItem,
  KvalitetaItem,
  MsanUredjajItem,
  Opcina,
  OpcinaLokacijeGroup,
  OpcineGeoJson,
  PretragaResponse,
  PrijavaResponse,
  Radnik,
  RezervirajResponse,
  Statistike,
  TestEmailResponse,
} from '@/types/api'
import { authStorage } from '@/lib/authStorage'
import { formatApiDetail } from '@/lib/apiErrors'

export { mapApiError } from '@/lib/apiErrors'

const BASE = import.meta.env.VITE_API_URL ?? '/api'

type RequestOptions = RequestInit & { skipAuth?: boolean }

async function downloadPdf(path: string, filename: string): Promise<void> {
  const token = authStorage.getToken()
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (res.status === 401) {
    authStorage.clear()
    window.location.href = '/prijava'
    throw new Error('Sesija je istekla.')
  }
  if (!res.ok) {
    let detail: unknown = 'Preuzimanje nije uspjelo.'
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      detail = res.statusText
    }
    throw new Error(formatApiDetail(detail))
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function request<T>(path: string, init?: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  }

  if (!init?.skipAuth) {
    const token = authStorage.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 401 && !init?.skipAuth) {
    authStorage.clear()
    window.location.href = '/prijava'
    throw new Error('Sesija je istekla. Prijavite se ponovo.')
  }

  if (!res.ok) {
    let detail: unknown = 'Došlo je do greške.'
    try {
      const body = await res.json()
      detail = body.detail ?? (typeof body === 'string' ? body : detail)
    } catch {
      detail = res.statusText || 'Došlo je do greške.'
    }
    throw new Error(formatApiDetail(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/health', { skipAuth: true }),

  prijava: (email: string, lozinka: string) =>
    request<PrijavaResponse>('/prijava', {
      method: 'POST',
      body: JSON.stringify({ email, lozinka }),
      skipAuth: true,
    }),

  statistike: () => request<Statistike>('/statistike'),

  opcine: (params?: { samo_s_brojevima?: boolean; pretraga?: string }) => {
    const q = new URLSearchParams()
    if (params?.samo_s_brojevima) q.set('samo_s_brojevima', 'true')
    if (params?.pretraga?.trim()) q.set('pretraga', params.pretraga.trim())
    const qs = q.toString()
    return request<Opcina[]>(`/opcine${qs ? `?${qs}` : ''}`)
  },

  opcineGeoJson: () => request<OpcineGeoJson>('/opcine/geojson'),

  korisnici: () => request<KorisnikItem[]>('/korisnici'),

  lokacijeHijerarhija: () => request<OpcinaLokacijeGroup[]>('/lokacije-hijerarhija'),

  msanUredjaji: () => request<MsanUredjajItem[]>('/msan-uredjaji'),

  kvalitete: () => request<KvalitetaItem[]>('/kvalitete'),

  pretraga: (params: Record<string, string | number | undefined>) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') q.set(k, String(v))
    })
    return request<PretragaResponse>(`/msisdn/pretraga?${q}`)
  },

  provjeriJmbg: (jmbg: string, ime?: string, prezime?: string) => {
    const q = new URLSearchParams({ jmbg })
    if (ime?.trim()) q.set('ime', ime.trim())
    if (prezime?.trim()) q.set('prezime', prezime.trim())
    return request<import('@/types/api').ProvjeriJmbgResponse>(`/msisdn/provjeri-jmbg?${q}`)
  },

  dodijeliBroj: (body: {
    opcina_naziv: string
    ime: string
    prezime: string
    jmbg: string
    email: string
    adresa: string
    grad: string
    postanski_broj: string
    msisdn_id?: number
    kvaliteta_id?: number
    placanje?: PlacanjePodaci
  }) =>
    request<DodijeliResponse>('/dodijeli-broj', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  dodijeliBulk: (body: {
    opcina_naziv: string
    broj_brojeva: number
    korisnik_ime: string
    korisnik_prezime: string
    korisnik_jmbg: string
    korisnik_email: string
    adresa: string
    grad: string
    postanski_broj: string
    kvaliteta_naziv?: string
    placanje?: PlacanjePodaci
  }) =>
    request<DodijeliBulkResponse>('/dodijeli-bulk', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  preuzmiRacun: (msisdnId: number) => downloadPdf(`/msisdn/${msisdnId}/racun`, `racun_${msisdnId}.pdf`),

  preuzmiUgovor: (msisdnId: number) => downloadPdf(`/msisdn/${msisdnId}/ugovor`, `ugovor_${msisdnId}.pdf`),

  dodjeleHeatmap: (dana = 90) =>
    request<import('@/types/api').DodjeleHeatmapResponse>(
      `/admin/statistika/dodjele-heatmap?dana=${dana}`,
    ),

  auditLogList: (params?: {
    radnik_id?: number
    entitet?: string
    od?: string
    do?: string
    q?: string
    limit?: number
    offset?: number
  }) => {
    const q = new URLSearchParams()
    if (params?.radnik_id != null) q.set('radnik_id', String(params.radnik_id))
    if (params?.entitet) q.set('entitet', params.entitet)
    if (params?.od) q.set('od', params.od)
    if (params?.do) q.set('do', params.do)
    if (params?.q) q.set('q', params.q)
    if (params?.limit != null) q.set('limit', String(params.limit))
    if (params?.offset != null) q.set('offset', String(params.offset))
    const qs = q.toString()
    return request<import('@/types/api').AuditLogListResponse>(
      `/admin/audit-log${qs ? `?${qs}` : ''}`,
    )
  },

  auditLogExportCsv: async (params?: {
    entitet?: string
    od?: string
    do?: string
    q?: string
  }) => {
    const q = new URLSearchParams()
    if (params?.entitet) q.set('entitet', params.entitet)
    if (params?.od) q.set('od', params.od)
    if (params?.do) q.set('do', params.do)
    if (params?.q) q.set('q', params.q)
    const token = authStorage.getToken()
    const res = await fetch(`${BASE}/admin/audit-log/export.csv?${q}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Export nije uspio')
    return res.blob()
  },

  portabilnostLista: (tip?: string) =>
    request<import('@/types/api').PortabilnostItem[]>(
      `/portabilnost${tip ? `?tip=${encodeURIComponent(tip)}` : ''}`,
    ),

  portabilnostKreiraj: (body: {
    tip: string
    izvor_op: string
    ciljni_op: string
    msisdn_id?: number
    broj?: string
    napomena?: string
  }) =>
    request<import('@/types/api').PortabilnostItem>('/portabilnost', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  portabilnostAzuriraj: (id: number, body: { status?: string; napomena?: string }) =>
    request<import('@/types/api').PortabilnostItem>(`/portabilnost/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  servisniNaloziLista: () =>
    request<import('@/types/api').ServisniNalogItem[]>('/servisni-nalozi'),

  servisniNalogKreiraj: (body: { uredjaj_id: number; opis: string; prioritet?: string }) =>
    request<import('@/types/api').ServisniNalogItem>('/servisni-nalozi', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  servisniNalogAzuriraj: (
    id: number,
    body: { status?: string; prioritet?: string; opis?: string },
  ) =>
    request<import('@/types/api').ServisniNalogItem>(`/servisni-nalozi/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  wildcardPretraga: (params: {
    uzorak: string
    opcina_naziv?: string
    kvaliteta_id?: number
    limit?: number
  }) => {
    const q = new URLSearchParams({ uzorak: params.uzorak })
    if (params.opcina_naziv) q.set('opcina_naziv', params.opcina_naziv)
    if (params.kvaliteta_id != null) q.set('kvaliteta_id', String(params.kvaliteta_id))
    if (params.limit != null) q.set('limit', String(params.limit))
    return request<import('@/types/api').WildcardPretragaResponse>(`/msisdn/wildcard?${q}`)
  },

  msisdnDetalj: (msisdnId: number) =>
    request<import('@/types/api').MsisdnDetalj>(`/msisdn/${msisdnId}`),

  patchKarantena: (
    msisdnId: number,
    body: { produzi_dana?: number; skrati_dana?: number; razlog?: string },
  ) =>
    request<import('@/types/api').KarantenaPatchResponse>(`/msisdn/${msisdnId}/karantena`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  oslobodiIzKarantene: (msisdnId: number, razlog?: string) =>
    request<{ poruka: string; msisdn_id: number; status: string }>(
      `/msisdn/${msisdnId}/oslobodi`,
      {
        method: 'POST',
        body: JSON.stringify(razlog ? { razlog } : {}),
      },
    ),

  vratiIzKaranteneAktivno: (msisdnId: number, razlog?: string) =>
    request<{ poruka: string; msisdn_id: number; status: string }>(
      `/msisdn/${msisdnId}/vrati-aktivno`,
      {
        method: 'POST',
        body: JSON.stringify(razlog ? { razlog } : {}),
      },
    ),

  oslobodi: (msisdnId: number, karantena_dana?: number) =>
    request<{ poruka: string }>(`/oslobodi/${msisdnId}`, {
      method: 'POST',
      body: JSON.stringify(karantena_dana != null ? { karantena_dana } : {}),
    }),

  rezerviraj: (msisdnId: number) =>
    request<RezervirajResponse>(`/rezerviraj/${msisdnId}`, { method: 'POST' }),

  rezervirajSljedeci: (
    opcinaNaziv: string,
    kvalitetaId?: number,
    excludeMsisdnId?: number,
  ) =>
    request<RezervirajResponse>('/rezerviraj-sljedeci', {
      method: 'POST',
      body: JSON.stringify({
        opcina_naziv: opcinaNaziv,
        ...(kvalitetaId != null ? { kvaliteta_id: kvalitetaId } : {}),
        ...(excludeMsisdnId != null ? { exclude_msisdn_id: excludeMsisdnId } : {}),
      }),
    }),

  ponistiRezervaciju: (msisdnId: number) =>
    request<{ poruka: string }>(`/rezerviraj/${msisdnId}`, { method: 'DELETE' }),

  listaRadnika: () => request<Radnik[]>('/radnici'),

  kreirajRadnika: (body: {
    email: string
    ime: string
    prezime: string
    lozinka: string
    uloga: string
    aktivan?: boolean
    jmbg?: string
  }) =>
    request<Radnik>('/radnici', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  azurirajRadnika: (
    id: number,
    body: Partial<{
      email: string
      ime: string
      prezime: string
      lozinka: string
      uloga: string
      aktivan: boolean
    }>,
  ) =>
    request<Radnik>(`/radnici/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  deaktivirajRadnika: (id: number) =>
    request<void>(`/radnici/${id}`, { method: 'DELETE' }),

  izvozStatistikeExcel: async () => {
    const token = (await import('@/lib/authStorage')).authStorage.getToken()
    const res = await fetch(`${BASE}/izvoz/statistike/excel`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Izvoz nije uspio')
    return res.blob()
  },

  izvozStatistikePdf: async () => {
    const token = (await import('@/lib/authStorage')).authStorage.getToken()
    const res = await fetch(`${BASE}/izvoz/statistike/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) throw new Error('Izvoz nije uspio')
    return res.blob()
  },

  importRak: async (file: File) => {
    const token = authStorage.getToken()
    const form = new FormData()
    form.append('datoteka', file)
    const res = await fetch(`${BASE}/admin/import-rak`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    })
    if (res.status === 401) {
      authStorage.clear()
      window.location.href = '/prijava'
      throw new Error('Sesija je istekla.')
    }
    if (!res.ok) {
      let detail = 'Import nije uspio.'
      try {
        const body = await res.json()
        detail = body.detail ?? detail
      } catch {
        detail = res.statusText
      }
      if (res.status === 404) {
        detail =
          'Endpoint nije pronađen. Restartajte backend (scripts/start-backend.ps1) i provjerite http://127.0.0.1:8000/docs — treba postojati POST /admin/import-rak.'
      }
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }
    return res.json() as Promise<ImportRakResponse>
  },

  testEmail: (to_email: string) =>
    request<TestEmailResponse>('/test-email', {
      method: 'POST',
      body: JSON.stringify({ to_email }),
    }),

  hijerarhijaTree: () => request<HijerarhijaEntitetGroup[]>('/hijerarhija/tree'),

  hijerarhijaOpcina: (opcinaId: number) =>
    request<HijerarhijaOpcinaDetail>(`/hijerarhija/opcina/${opcinaId}`),

  hijerarhijaPretragaPb: (pb: string) =>
    request<HijerarhijaPretragaPb>(`/hijerarhija/pretraga?pb=${encodeURIComponent(pb)}`),

  hijerarhijaStablo: () =>
    request<import('@/types/api').HijerarhijaStabloZupanija[]>('/hijerarhija/stablo'),

  hijerarhijaCvor: (tip: string, id: number) =>
    request<import('@/types/api').HijerarhijaCvorDetalj>(
      `/hijerarhija/cvor?tip=${encodeURIComponent(tip)}&id=${id}`,
    ),

  importPostanskiUredi: (path?: string) =>
    request<ImportPostanskiResponse>('/admin/import-postanski-uredi', {
      method: 'POST',
      body: JSON.stringify(path ? { path } : {}),
    }),

  emailLogList: (params?: { limit?: number; offset?: number; status?: string; msisdn_id?: number }) => {
    const q = new URLSearchParams()
    if (params?.limit != null) q.set('limit', String(params.limit))
    if (params?.offset != null) q.set('offset', String(params.offset))
    if (params?.status) q.set('status', params.status)
    if (params?.msisdn_id != null) q.set('msisdn_id', String(params.msisdn_id))
    const qs = q.toString()
    return request<import('@/types/api').EmailLogListResponse>(
      `/admin/email-log${qs ? `?${qs}` : ''}`,
    )
  },

  emailLogHtml: (logId: number) =>
    request<{ html: string }>(`/admin/email-log/${logId}/html`),

  emailResend: (logId: number) =>
    request<import('@/types/api').EmailResendResponse>(`/admin/email-resend/${logId}`, {
      method: 'POST',
    }),
}
