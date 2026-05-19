import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Clock, RefreshCw, X } from 'lucide-react'
import { api } from '@/lib/api'
import type { KvalitetaItem, Opcina } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
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

interface DodjelaFormaProps {
  onSuccess?: () => void
  initialMsisdnId?: number
}

export function DodjelaForma({ onSuccess, initialMsisdnId }: DodjelaFormaProps) {
  const [opcine, setOpcine] = useState<Opcina[]>([])
  const [kvalitete, setKvalitete] = useState<KvalitetaItem[]>([])
  const [opcina, setOpcina] = useState('Mostar')
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
  const { formatTime, expired } = useReservationTimer(timerInit)

  useEffect(() => {
    Promise.all([api.opcine(), api.kvalitete()])
      .then(([o, k]) => {
        setOpcine(o)
        setKvalitete(k)
        if (k.length) setKvalitetaId(String(k[0].id))
      })
      .catch(() => toast.error('Greška pri učitavanju podataka'))
  }, [])

  const odabranaKvaliteta = useMemo(
    () => kvalitete.find((k) => String(k.id) === kvalitetaId),
    [kvalitete, kvalitetaId],
  )

  const jmbgError =
    jmbg.length === 13 && !validirajJmbg(jmbg) ? 'Neispravan JMBG (modul 11)' : undefined

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

  const rezervirajSljedeci = useCallback(async () => {
    try {
      if (rezerviranIdRef.current) {
        await api.ponistiRezervaciju(rezerviranIdRef.current).catch(() => {})
        rezerviranIdRef.current = null
      }
      const kid = kvalitetaId ? Number(kvalitetaId) : undefined
      const rez = await api.rezervirajSljedeci(opcina, kid)
      rezerviranIdRef.current = rez.msisdn_id
      setRezerviranId(rez.msisdn_id)
      setRezerviraniBroj(rez.broj_formatiran)
      setTimerInit(rez.preostalo_sekundi)
      toast.success(`Broj ${rez.broj_formatiran} rezerviran na 5 minuta`)
    } catch (e) {
      setRezerviranId(null)
      setRezerviraniBroj(null)
      setTimerInit(null)
      rezerviranIdRef.current = null
      toast.error(e instanceof Error ? e.message : 'Greška pri rezervaciji')
    }
  }, [opcina, kvalitetaId])

  const rezervirajOdabrani = useCallback(async (msisdnId: number) => {
    try {
      if (rezerviranIdRef.current) {
        await api.ponistiRezervaciju(rezerviranIdRef.current).catch(() => {})
      }
      const rez = await api.rezerviraj(msisdnId)
      rezerviranIdRef.current = rez.msisdn_id
      setRezerviranId(rez.msisdn_id)
      setRezerviraniBroj(rez.broj_formatiran)
      setTimerInit(rez.preostalo_sekundi)
      toast.success(`Broj ${rez.broj_formatiran} rezerviran na 5 minuta`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška pri rezervaciji')
    }
  }, [])

  useEffect(() => {
    if (initialMsisdnId) {
      void rezervirajOdabrani(initialMsisdnId)
      return () => {
        const id = rezerviranIdRef.current
        if (id) api.ponistiRezervaciju(id).catch(() => {})
      }
    }
    void rezervirajSljedeci()
    return () => {
      const id = rezerviranIdRef.current
      if (id) api.ponistiRezervaciju(id).catch(() => {})
    }
  }, [initialMsisdnId, opcina, kvalitetaId, rezervirajSljedeci, rezervirajOdabrani])

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
    if (!validirajJmbg(jmbg)) {
      toast.error('Neispravan JMBG')
      return
    }
    if (!rezerviranId) {
      toast.error('Nema aktivne rezervacije broja. Pričekajte rezervaciju ili odaberite općinu ponovo.')
      return
    }
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
      rezerviranIdRef.current = null
      setRezerviranId(null)
      setRezerviraniBroj(null)
      setTimerInit(null)
      onSuccess?.()
      void rezervirajSljedeci()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Greška pri dodjeli')
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
                <Button type="button" variant="outline" size="sm" onClick={() => void rezervirajSljedeci()}>
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
            <Select
              label="Općina"
              value={opcina}
              onValueChange={setOpcina}
              options={opcine.map((o) => ({
                value: o.naziv,
                label: `${o.naziv} (${(o.broj_msisdn ?? 0).toLocaleString('hr-HR')})`,
              }))}
            />
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
              onChange={(e) => setJmbg(e.target.value.replace(/\D/g, '').slice(0, 13))}
              maxLength={13}
              error={jmbgError}
              required
            />
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
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
              onChange={(e) => setPostanskiBroj(e.target.value)}
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
    </>
  )
}
