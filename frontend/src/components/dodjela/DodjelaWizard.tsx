import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, ChevronLeft, ChevronRight, Clock, RefreshCw, Search, Sparkles, X } from 'lucide-react'
import { api, mapApiError } from '@/lib/api'
import type { KvalitetaItem, Opcina, ProvjeriJmbgResponse } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { useReservationTimer } from '@/hooks/useReservationTimer'
import { PlacanjePolja, type NacinPlacanja } from '@/components/dodjela/PlacanjePolja'
import { DodjelaSuccessModal, type DodjelaDokumentStavka } from '@/components/dodjela/DodjelaSuccessModal'
import { cn } from '@/lib/utils'

function validirajJmbg(jmbg: string): boolean {
  if (!/^\d{13}$/.test(jmbg)) return false
  const w = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
  let s = 0
  for (let i = 0; i < 12; i++) s += parseInt(jmbg[i], 10) * w[i]
  let k = 11 - (s % 11)
  if (k === 10 || k === 11) k = 0
  return k === parseInt(jmbg[12], 10)
}

function validirajEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

function validirajPostanskiBroj(pb: string): boolean {
  const t = pb.trim()
  return !t || /^\d{5}$/.test(t)
}

const KORACI = ['Broj', 'Kupac', 'Plaćanje'] as const

interface DodjelaWizardProps {
  onSuccess?: () => void
  initialMsisdnId?: number
}

export function DodjelaWizard({ onSuccess, initialMsisdnId }: DodjelaWizardProps) {
  const [korak, setKorak] = useState(1)
  const [opcine, setOpcine] = useState<Opcina[]>([])
  const [kvalitete, setKvalitete] = useState<KvalitetaItem[]>([])
  const [opcina, setOpcina] = useState('Mostar')
  const [opcinaPretraga, setOpcinaPretraga] = useState('')
  const [kvalitetaId, setKvalitetaId] = useState('')
  const [ime, setIme] = useState('')
  const [prezime, setPrezime] = useState('')
  const [jmbg, setJmbg] = useState('')
  const [email, setEmail] = useState('')
  const [adresa, setAdresa] = useState('')
  const [grad, setGrad] = useState('')
  const [postanskiBroj, setPostanskiBroj] = useState('')
  const [nacinPlacanja, setNacinPlacanja] = useState<NacinPlacanja>('gotovina')
  const [brojKartice, setBrojKartice] = useState('')
  const [datumIsteka, setDatumIsteka] = useState('')
  const [cvv, setCvv] = useState('')
  const [imeVlasnika, setImeVlasnika] = useState('')
  const [loading, setLoading] = useState(false)
  const [rezerviranId, setRezerviranId] = useState<number | null>(null)
  const [rezerviraniBroj, setRezerviraniBroj] = useState<string | null>(null)
  const [timerInit, setTimerInit] = useState<number | null>(null)
  const rezerviranIdRef = useRef<number | null>(null)
  const [catalogReady, setCatalogReady] = useState(false)
  const [jmbgProvjera, setJmbgProvjera] = useState<ProvjeriJmbgResponse | null>(null)
  const [jmbgProvjeraLoading, setJmbgProvjeraLoading] = useState(false)
  const [successOpen, setSuccessOpen] = useState(false)
  const [dokumenti, setDokumenti] = useState<DodjelaDokumentStavka[]>([])
  const [emailError, setEmailError] = useState<string | undefined>()
  const [postanskiError, setPostanskiError] = useState<string | undefined>()
  const [jmbgSubmitError, setJmbgSubmitError] = useState<string | undefined>()
  const { formatTime, expired } = useReservationTimer(timerInit)

  useEffect(() => {
    Promise.all([api.opcine(), api.kvalitete()])
      .then(([o, k]) => {
        setOpcine(o)
        setKvalitete(k)
        if (k.length) setKvalitetaId(String(k[0].id))
        setCatalogReady(true)
      })
      .catch((e) => toast.error(mapApiError(e, 'Katalog općina/kvaliteta nije učitan.')))
  }, [])

  const odabranaKvaliteta = useMemo(
    () => kvalitete.find((k) => String(k.id) === kvalitetaId),
    [kvalitete, kvalitetaId],
  )

  const opcineFiltrirane = useMemo(() => {
    const q = opcinaPretraga.trim().toLowerCase()
    if (!q) return opcine
    return opcine.filter((o) => o.naziv.toLowerCase().includes(q))
  }, [opcine, opcinaPretraga])

  const opcineOptions = useMemo(
    () =>
      opcineFiltrirane.map((o) => ({
        value: o.naziv,
        label: `${o.naziv} (${(o.broj_msisdn ?? 0).toLocaleString('hr-HR')})`,
      })),
    [opcineFiltrirane],
  )

  useEffect(() => {
    if (!opcine.length) return
    if (!opcine.some((o) => o.naziv === opcina)) {
      setOpcina(opcine.some((o) => o.naziv === 'Mostar') ? 'Mostar' : opcine[0].naziv)
    }
  }, [opcine, opcina])

  const jmbgError =
    jmbg.length === 13 && !validirajJmbg(jmbg) ? 'Neispravan JMBG (modul 11)' : undefined

  useEffect(() => {
    if (jmbg.length !== 13 || !validirajJmbg(jmbg)) {
      setJmbgProvjera(null)
      setJmbgProvjeraLoading(false)
      return
    }
    let active = true
    const t = window.setTimeout(() => {
      setJmbgProvjeraLoading(true)
      api
        .provjeriJmbg(jmbg, ime, prezime)
        .then((res) => {
          if (active) setJmbgProvjera(res)
        })
        .catch(() => {
          if (active) setJmbgProvjera(null)
        })
        .finally(() => {
          if (active) setJmbgProvjeraLoading(false)
        })
    }, 400)
    return () => {
      active = false
      window.clearTimeout(t)
    }
  }, [jmbg, ime, prezime])

  const ponistiRezervaciju = useCallback(async () => {
    const id = rezerviranIdRef.current
    if (!id) return
    try {
      await api.ponistiRezervaciju(id)
    } catch {
      /* cleanup */
    }
    rezerviranIdRef.current = null
    setRezerviranId(null)
    setRezerviraniBroj(null)
    setTimerInit(null)
  }, [])

  const rezervirajSljedeci = useCallback(
    async (showToast = true) => {
      try {
        const prevId = rezerviranIdRef.current
        if (prevId) await api.ponistiRezervaciju(prevId).catch(() => {})
        const kid = kvalitetaId ? Number(kvalitetaId) : undefined
        const rez = await api.rezervirajSljedeci(opcina, kid, prevId ?? undefined)
        rezerviranIdRef.current = rez.msisdn_id
        setRezerviranId(rez.msisdn_id)
        setRezerviraniBroj(rez.broj_formatiran)
        setTimerInit(rez.preostalo_sekundi)
        if (showToast) toast.success(`Broj ${rez.broj_formatiran} rezerviran na 5 minuta`)
      } catch (e) {
        rezerviranIdRef.current = null
        setRezerviranId(null)
        setRezerviraniBroj(null)
        setTimerInit(null)
        toast.error(mapApiError(e, 'Rezervacija broja nije uspjela.'))
      }
    },
    [opcina, kvalitetaId],
  )

  useEffect(() => {
    if (!catalogReady) return
    let active = true
    const run = async () => {
      try {
        if (rezerviranIdRef.current) {
          await api.ponistiRezervaciju(rezerviranIdRef.current).catch(() => {})
          rezerviranIdRef.current = null
        }
        const rez = initialMsisdnId
          ? await api.rezerviraj(initialMsisdnId)
          : await api.rezervirajSljedeci(opcina, kvalitetaId ? Number(kvalitetaId) : undefined)
        if (!active) {
          await api.ponistiRezervaciju(rez.msisdn_id).catch(() => {})
          return
        }
        rezerviranIdRef.current = rez.msisdn_id
        setRezerviranId(rez.msisdn_id)
        setRezerviraniBroj(rez.broj_formatiran)
        setTimerInit(rez.preostalo_sekundi)
        toast.success(`Broj ${rez.broj_formatiran} rezerviran na 5 minuta`)
      } catch (e) {
        if (!active) return
        rezerviranIdRef.current = null
        setRezerviranId(null)
        setRezerviraniBroj(null)
        setTimerInit(null)
        toast.error(mapApiError(e, 'Rezervacija broja nije uspjela.'))
      }
    }
    void run()
    return () => {
      active = false
      const id = rezerviranIdRef.current
      if (id) {
        api.ponistiRezervaciju(id).catch(() => {})
        rezerviranIdRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogReady, initialMsisdnId])

  const buildPlacanje = () => ({
    nacin: nacinPlacanja,
    ...(nacinPlacanja === 'kartica'
      ? { broj_kartice: brojKartice, datum_isteka: datumIsteka, cvv, ime_vlasnika: imeVlasnika }
      : {}),
  })

  const mozeKorak2 = Boolean(rezerviranId && !expired)
  const mozeKorak3 = Boolean(
    ime.trim() &&
      prezime.trim() &&
      jmbg.length === 13 &&
      validirajJmbg(jmbg) &&
      validirajEmail(email) &&
      adresa.trim() &&
      grad.trim() &&
      validirajPostanskiBroj(postanskiBroj),
  )

  const daljeIzK1 = () => {
    if (!mozeKorak2) {
      toast.error('Rezervirajte broj prije nastavka (timer ne smije biti istekao).')
      return
    }
    setKorak(2)
  }

  const daljeIzK2 = () => {
    const jErr =
      jmbg.length !== 13 || !validirajJmbg(jmbg)
        ? 'Unesite ispravan JMBG (13 znamenki, modul 11).'
        : undefined
    const eErr = !validirajEmail(email) ? 'Unesite ispravnu email adresu.' : undefined
    const pErr = !validirajPostanskiBroj(postanskiBroj)
      ? 'Poštanski broj mora imati točno 5 znamenki.'
      : undefined
    setJmbgSubmitError(jErr)
    setEmailError(eErr)
    setPostanskiError(pErr)
    if (jErr || eErr || pErr || !adresa.trim() || !grad.trim() || !ime.trim() || !prezime.trim()) {
      toast.error('Popunite sva polja kupca.')
      return
    }
    setKorak(3)
  }

  const izvrsiDodjelu = async () => {
    if (!rezerviranId) return
    setLoading(true)
    try {
      const res = await api.dodijeliBroj({
        opcina_naziv: opcina,
        ime,
        prezime,
        jmbg,
        email,
        adresa,
        grad,
        postanski_broj: postanskiBroj,
        msisdn_id: rezerviranId,
        kvaliteta_id: kvalitetaId ? Number(kvalitetaId) : undefined,
        placanje: buildPlacanje(),
      })
      toast.success(`Broj ${res.broj_formatiran} uspješno dodijeljen (${res.kvaliteta})`)
      if (res.email_poslan) toast.info('Račun poslan na email (ugovor preuzmite u aplikaciji)')
      setDokumenti([
        {
          msisdn_id: res.msisdn_id,
          broj_formatiran: res.broj_formatiran,
          racun_url: res.racun_url,
          ugovor_url: res.ugovor_url,
        },
      ])
      setSuccessOpen(true)
      onSuccess?.()
      setKorak(1)
      rezerviranIdRef.current = null
      setRezerviranId(null)
      setRezerviraniBroj(null)
      setTimerInit(null)
      void rezervirajSljedeci(false)
    } catch (err) {
      toast.error(mapApiError(err, 'Dodjela broja nije uspjela.'))
    } finally {
      setLoading(false)
    }
  }

  const rezervacijaBanner =
    rezerviranId != null || timerInit != null ? (
      <div
        className={cn(
          'mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3',
          expired
            ? 'border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40'
            : 'border-[#00A3E0]/30 bg-[#e6f7fc] dark:bg-[#0054A6]/10',
        )}
      >
        <div className="text-sm text-[#0054A6] dark:text-[#00A3E0]">
          {rezerviraniBroj && <p className="text-base font-semibold">{rezerviraniBroj}</p>}
          <span className="flex items-center gap-2 font-medium">
            <Clock className="h-4 w-4" />
            {expired ? 'Rezervacija je istekla' : `Rezervacija ističe za: ${formatTime()}`}
          </span>
        </div>
        <span className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void rezervirajSljedeci()}>
            <RefreshCw className="h-4 w-4" />
            Novi broj
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => void ponistiRezervaciju()}>
            <X className="h-4 w-4" />
          </Button>
        </span>
      </div>
    ) : null

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[#0054A6]" />
            Čarobnjak dodjele
          </CardTitle>
          <div className="flex gap-2 pt-2">
            {KORACI.map((label, i) => {
              const n = i + 1
              const aktivan = korak === n
              const gotov = korak > n
              return (
                <span
                  key={label}
                  className={cn(
                    'rounded-full px-3 py-1 text-xs font-medium',
                    aktivan && 'bg-[#0054A6] text-white',
                    gotov && !aktivan && 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
                    !aktivan && !gotov && 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
                  )}
                >
                  {n}. {label}
                </span>
              )
            })}
          </div>
        </CardHeader>
        <CardContent>
          {korak === 1 && (
            <div className="space-y-4">
              {rezervacijaBanner}
              <span className="space-y-2 block">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Općina</label>
                <div className="flex items-center gap-2 rounded-lg border border-slate-200 px-2.5 py-1.5 dark:border-slate-700">
                  <Search className="h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    value={opcinaPretraga}
                    onChange={(e) => setOpcinaPretraga(e.target.value)}
                    placeholder="Pretraži općinu…"
                    className="flex-1 bg-transparent text-sm outline-none dark:text-slate-100"
                  />
                </div>
                {opcineOptions.length > 0 && (
                  <Select value={opcina} onValueChange={setOpcina} options={opcineOptions} />
                )}
              </span>
              <Select
                label="Kvaliteta broja"
                value={kvalitetaId}
                onValueChange={setKvalitetaId}
                options={kvalitete.map((k) => ({
                  value: String(k.id),
                  label: `${k.naziv} – ${k.cijena.toFixed(2)} KM`,
                }))}
              />
              {odabranaKvaliteta && (
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Cijena s PDV: <strong>{(odabranaKvaliteta.cijena * 1.17).toFixed(2)} KM</strong>
                </p>
              )}
            </div>
          )}

          {korak === 2 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {rezervacijaBanner}
              <Input label="Ime" value={ime} onChange={(e) => setIme(e.target.value)} required />
              <Input label="Prezime" value={prezime} onChange={(e) => setPrezime(e.target.value)} required />
              <Input
                label="JMBG"
                value={jmbg}
                onChange={(e) => {
                  setJmbg(e.target.value.replace(/\D/g, '').slice(0, 13))
                  setJmbgSubmitError(undefined)
                }}
                maxLength={13}
                error={jmbgSubmitError ?? jmbgError}
                required
              />
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setEmailError(undefined)
                }}
                error={emailError}
                required
              />
              <Input
                label="Adresa"
                value={adresa}
                onChange={(e) => setAdresa(e.target.value)}
                className="sm:col-span-2"
                required
              />
              <Input label="Grad" value={grad} onChange={(e) => setGrad(e.target.value)} required />
              <Input
                label="Poštanski broj"
                value={postanskiBroj}
                onChange={(e) => {
                  setPostanskiBroj(e.target.value.replace(/\D/g, '').slice(0, 5))
                  setPostanskiError(undefined)
                }}
                maxLength={5}
                error={postanskiError}
                required
              />
              {(jmbgProvjeraLoading || (jmbgProvjera?.upozorenja.length ?? 0) > 0) && (
                <div className="sm:col-span-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
                  {jmbgProvjeraLoading ? (
                    <p>Provjera JMBG-a…</p>
                  ) : (
                    <ul className="space-y-1">
                      {jmbgProvjera?.upozorenja.map((u) => (
                        <li key={u} className="flex gap-2">
                          <AlertTriangle className="h-4 w-4 shrink-0" />
                          {u}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}

          {korak === 3 && (
            <div className="space-y-4">
              {rezervacijaBanner}
              <dl className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 text-sm dark:border-slate-800 dark:bg-slate-900/50">
                <div className="flex justify-between gap-2 border-b border-slate-200 py-2 dark:border-slate-700">
                  <dt className="text-slate-600 dark:text-slate-400">Broj</dt>
                  <dd className="font-mono font-semibold text-[#0054A6] dark:text-[#00A3E0]">
                    {rezerviraniBroj}
                  </dd>
                </div>
                <div className="flex justify-between gap-2 border-b border-slate-200 py-2 dark:border-slate-700">
                  <dt className="text-slate-600 dark:text-slate-400">Kupac</dt>
                  <dd className="text-right">
                    {ime} {prezime}
                  </dd>
                </div>
                <div className="flex justify-between gap-2 py-2">
                  <dt className="text-slate-600 dark:text-slate-400">Općina / kvaliteta</dt>
                  <dd className="text-right capitalize">
                    {opcina} · {odabranaKvaliteta?.naziv}
                  </dd>
                </div>
              </dl>
              <PlacanjePolja
                nacin={nacinPlacanja}
                onNacinChange={setNacinPlacanja}
                brojKartice={brojKartice}
                onBrojKarticeChange={setBrojKartice}
                datumIsteka={datumIsteka}
                onDatumIstekaChange={setDatumIsteka}
                cvv={cvv}
                onCvvChange={setCvv}
                imeVlasnika={imeVlasnika}
                onImeVlasnikaChange={setImeVlasnika}
              />
            </div>
          )}

          <div className="mt-6 flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              disabled={korak <= 1}
              onClick={() => setKorak((k) => Math.max(1, k - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Natrag
            </Button>
            {korak < 3 ? (
              <Button
                type="button"
                onClick={korak === 1 ? daljeIzK1 : daljeIzK2}
                disabled={korak === 1 ? !mozeKorak2 : !mozeKorak3}
              >
                Dalje
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button type="button" loading={loading} onClick={() => void izvrsiDodjelu()}>
                Potvrdi dodjelu
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <DodjelaSuccessModal open={successOpen} onOpenChange={setSuccessOpen} stavke={dokumenti} />
    </>
  )
}
