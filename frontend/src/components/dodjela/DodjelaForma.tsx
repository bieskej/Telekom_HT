import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, Clock, RefreshCw, Search, X } from 'lucide-react'
import { api, mapApiError } from '@/lib/api'
import type { KvalitetaItem, Opcina, ProvjeriJmbgResponse } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Dialog } from '@/components/ui/Dialog'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { useReservationTimer } from '@/hooks/useReservationTimer'
import { PlacanjePolja, type NacinPlacanja } from '@/components/dodjela/PlacanjePolja'
import { DodjelaSuccessModal, type DodjelaDokumentStavka } from '@/components/dodjela/DodjelaSuccessModal'

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

function validirajPostanskiBroj(postanskiBroj: string): boolean {
  const t = postanskiBroj.trim()
  return !t || /^\d{5}$/.test(t)
}

interface DodjelaFormaProps {
  onSuccess?: () => void
  initialMsisdnId?: number
}

export function DodjelaForma({ onSuccess, initialMsisdnId }: DodjelaFormaProps) {
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
  const [successOpen, setSuccessOpen] = useState(false)
  const [dokumenti, setDokumenti] = useState<DodjelaDokumentStavka[]>([])
  const [catalogReady, setCatalogReady] = useState(false)
  const [jmbgProvjera, setJmbgProvjera] = useState<ProvjeriJmbgResponse | null>(null)
  const [jmbgProvjeraLoading, setJmbgProvjeraLoading] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
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
    const imaMostar = opcine.some((o) => o.naziv === 'Mostar')
    if (!opcine.some((o) => o.naziv === opcina)) {
      setOpcina(imaMostar ? 'Mostar' : opcine[0].naziv)
    }
  }, [opcine, opcina])

  useEffect(() => {
    if (opcineOptions.length === 0) return
    if (!opcineOptions.some((o) => o.value === opcina)) {
      setOpcina(opcineOptions[0].value)
    }
  }, [opcineOptions, opcina])

  const jmbgError =
    jmbg.length === 13 && !validirajJmbg(jmbg) ? 'Neispravan JMBG (modul 11)' : undefined

  useEffect(() => {
    if (jmbg.length !== 13 || !validirajJmbg(jmbg)) {
      setJmbgProvjera(null)
      setJmbgProvjeraLoading(false)
      return
    }
    let active = true
    const timer = window.setTimeout(() => {
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
      window.clearTimeout(timer)
    }
  }, [jmbg, ime, prezime])

  const ponistiAktivnuRezervaciju = useCallback(async () => {
    const id = rezerviranIdRef.current
    if (!id) return
    try {
      await api.ponistiRezervaciju(id)
    } catch {
      /* ignoriraj pri cleanupu */
    }
    rezerviranIdRef.current = null
    setRezerviranId(null)
    setRezerviraniBroj(null)
    setTimerInit(null)
  }, [])

  const rezervirajSljedeci = useCallback(
    async (opts?: { toast?: boolean }) => {
      const showToast = opts?.toast !== false
      try {
        const prevId = rezerviranIdRef.current
        if (prevId) {
          await api.ponistiRezervaciju(prevId).catch(() => {})
          rezerviranIdRef.current = null
        }
        const kid = kvalitetaId ? Number(kvalitetaId) : undefined
        const rez = await api.rezervirajSljedeci(opcina, kid, prevId ?? undefined)
        rezerviranIdRef.current = rez.msisdn_id
        setRezerviranId(rez.msisdn_id)
        setRezerviraniBroj(rez.broj_formatiran)
        setTimerInit(rez.preostalo_sekundi)
        if (showToast) {
          toast.success(`Broj ${rez.broj_formatiran} rezerviran na 5 minuta`)
        }
      } catch (e) {
        setRezerviranId(null)
        setRezerviraniBroj(null)
        setTimerInit(null)
        rezerviranIdRef.current = null
        if (showToast) {
          toast.error(mapApiError(e, 'Rezervacija broja nije uspjela.'))
        }
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
        setRezerviranId(null)
        setRezerviraniBroj(null)
        setTimerInit(null)
        rezerviranIdRef.current = null
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- jednom nakon učitavanja kataloga
  }, [catalogReady, initialMsisdnId])

  const buildPlacanje = () => ({
    nacin: nacinPlacanja,
    ...(nacinPlacanja === 'kartica'
      ? {
          broj_kartice: brojKartice,
          datum_isteka: datumIsteka,
          cvv,
          ime_vlasnika: imeVlasnika,
        }
      : {}),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const jErr =
      jmbg.length !== 13 || !validirajJmbg(jmbg) ? 'Unesite ispravan JMBG (13 znamenki, modul 11).' : undefined
    const eErr = !validirajEmail(email) ? 'Unesite ispravnu email adresu.' : undefined
    const pErr = !validirajPostanskiBroj(postanskiBroj)
      ? 'Poštanski broj mora imati točno 5 znamenki.'
      : undefined
    setJmbgSubmitError(jErr)
    setEmailError(eErr)
    setPostanskiError(pErr)
    if (jErr || eErr || pErr) return
    if (!rezerviranId) {
      toast.error('Nema aktivne rezervacije broja. Pričekajte rezervaciju ili odaberite općinu ponovo.')
      return
    }
    setConfirmOpen(true)
  }

  const izvrsiDodjelu = async () => {
    if (!rezerviranId) return
    setConfirmOpen(false)
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
      if (res.email_poslan) {
        toast.info('Račun poslan na email (ugovor preuzmite u aplikaciji)')
      }
      setDokumenti([
        {
          msisdn_id: res.msisdn_id,
          broj_formatiran: res.broj_formatiran,
          racun_url: res.racun_url,
          ugovor_url: res.ugovor_url,
        },
      ])
      setSuccessOpen(true)
      setIme('')
      setPrezime('')
      setJmbg('')
      setEmail('')
      setAdresa('')
      setGrad('')
      setPostanskiBroj('')
      setBrojKartice('')
      setDatumIsteka('')
      setCvv('')
      setImeVlasnika('')
      setNacinPlacanja('gotovina')
      setJmbgProvjera(null)
      rezerviranIdRef.current = null
      setRezerviranId(null)
      setRezerviraniBroj(null)
      setTimerInit(null)
      onSuccess?.()
      void rezervirajSljedeci()
    } catch (err) {
      toast.error(mapApiError(err, 'Dodjela broja nije uspjela.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Card className="animate-fade-in">
        <CardHeader>
          <CardTitle>Dodjela broja</CardTitle>
        </CardHeader>
        <CardContent>
          {(rezerviranId != null || timerInit != null) && (
            <div
              className={`mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 ${
                expired ? 'border-amber-200 bg-amber-50' : 'border-[#00A3E0]/30 bg-[#e6f7fc]'
              }`}
            >
              <div className="flex flex-col gap-1 text-sm text-[#0054A6]">
                {rezerviraniBroj && (
                  <p className="text-base font-semibold tracking-tight">{rezerviraniBroj}</p>
                )}
                <div className="flex items-center gap-2 font-medium">
                  <Clock className="h-4 w-4 shrink-0" />
                  {expired ? 'Rezervacija je istekla' : `Rezervacija ističe za: ${formatTime()}`}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void rezervirajSljedeci({ toast: true })}
                >
                  <RefreshCw className="h-4 w-4" />
                  Novi broj
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => void ponistiAktivnuRezervaciju()}
                  disabled={!rezerviranId}
                >
                  <X className="h-4 w-4" />
                  Odustani
                </Button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-2">
            <span className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Općina</label>
              <div className="flex items-center gap-2 rounded-lg border border-slate-200 px-2.5 py-1.5">
                <Search className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                <input
                  type="text"
                  value={opcinaPretraga}
                  onChange={(e) => setOpcinaPretraga(e.target.value)}
                  placeholder="Pretraži općinu…"
                  className="flex-1 bg-transparent text-sm outline-none"
                />
              </div>
              {opcineOptions.length === 0 ? (
                <p className="text-xs text-slate-500">Nema općina za ovaj upit.</p>
              ) : (
                <Select
                  value={opcina}
                  onValueChange={setOpcina}
                  options={opcineOptions}
                />
              )}
            </span>
            <Select
              label="Kvaliteta broja"
              value={kvalitetaId}
              onValueChange={setKvalitetaId}
              options={kvalitete.map((k) => ({
                value: String(k.id),
                label: `${k.naziv.charAt(0).toUpperCase() + k.naziv.slice(1)} – ${k.cijena.toFixed(2)} KM`,
              }))}
            />
            {odabranaKvaliteta && (
              <p className="lg:col-span-2 rounded-xl bg-[#F5F5F5] px-4 py-3 text-sm text-slate-700">
                Cijena (bez PDV): <strong>{odabranaKvaliteta.cijena.toFixed(2)} KM</strong> · s PDV (17%):{' '}
                <strong>{(odabranaKvaliteta.cijena * 1.17).toFixed(2)} KM</strong>
              </p>
            )}
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
            {(jmbgProvjeraLoading || (jmbgProvjera?.upozorenja.length ?? 0) > 0) && (
              <div className="lg:col-span-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {jmbgProvjeraLoading ? (
                  <p>Provjera JMBG-a…</p>
                ) : (
                  <ul className="space-y-1">
                    {jmbgProvjera?.upozorenja.map((u) => (
                      <li key={u} className="flex items-start gap-2">
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                        <span>{u}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
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
              className="lg:col-span-2"
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
            <span className="lg:col-span-2">
              <Button type="submit" loading={loading} className="w-full sm:w-auto" size="lg">
                Dodijeli
              </Button>
            </span>
          </form>
        </CardContent>
      </Card>

      <DodjelaSuccessModal open={successOpen} onOpenChange={setSuccessOpen} stavke={dokumenti} />

      <Dialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Potvrda dodjele"
        description="Provjerite podatke prije dodjele broja."
      >
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Broj</dt>
            <dd className="font-mono font-semibold text-[#0054A6]">{rezerviraniBroj ?? '—'}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Općina</dt>
            <dd className="font-medium">{opcina}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Kvaliteta</dt>
            <dd className="font-medium capitalize">{odabranaKvaliteta?.naziv ?? '—'}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Korisnik</dt>
            <dd className="font-medium text-right">
              {ime} {prezime}
            </dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">JMBG</dt>
            <dd className="font-mono">{jmbg}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Email</dt>
            <dd>{email}</dd>
          </div>
          <div className="flex justify-between gap-4 border-b border-slate-100 py-2">
            <dt className="text-slate-500">Adresa</dt>
            <dd className="text-right">
              {adresa}, {postanskiBroj} {grad}
            </dd>
          </div>
        </dl>
        {(jmbgProvjera?.upozorenja.length ?? 0) > 0 && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="mb-2 flex items-center gap-2 font-medium">
              <AlertTriangle className="h-4 w-4" />
              Upozorenja
            </p>
            <ul className="list-inside list-disc space-y-1">
              {jmbgProvjera?.upozorenja.map((u) => (
                <li key={u}>{u}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => setConfirmOpen(false)}>
            Odustani
          </Button>
          <Button type="button" loading={loading} onClick={() => void izvrsiDodjelu()}>
            Potvrdi dodjelu
          </Button>
        </div>
      </Dialog>
    </>
  )
}
