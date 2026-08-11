import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { KvalitetaItem, Opcina } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { PlacanjePolja, type NacinPlacanja } from '@/components/dodjela/PlacanjePolja'
import { DodjelaSuccessModal, type DodjelaDokumentStavka } from '@/components/dodjela/DodjelaSuccessModal'

interface BulkDodjelaModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

function validirajJmbg(jmbg: string): boolean {
  if (!/^\d{13}$/.test(jmbg)) return false
  const w = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
  let s = 0
  for (let i = 0; i < 12; i++) s += parseInt(jmbg[i], 10) * w[i]
  let k = 11 - (s % 11)
  if (k === 10 || k === 11) k = 0
  return k === parseInt(jmbg[12], 10)
}

export function BulkDodjelaModal({ open, onOpenChange, onSuccess }: BulkDodjelaModalProps) {
  const [opcine, setOpcine] = useState<Opcina[]>([])
  const [kvalitete, setKvalitete] = useState<KvalitetaItem[]>([])
  const [opcina, setOpcina] = useState('Mostar')
  const [kvalitetaNaziv, setKvalitetaNaziv] = useState('silver')
  const [brojBrojeva, setBrojBrojeva] = useState(5)
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
  const [successOpen, setSuccessOpen] = useState(false)
  const [dokumenti, setDokumenti] = useState<DodjelaDokumentStavka[]>([])

  useEffect(() => {
    if (!open) return
    Promise.all([api.opcine(), api.kvalitete()])
      .then(([o, k]) => {
        setOpcine(o)
        setKvalitete(k)
        if (k.length) setKvalitetaNaziv((prev) => (k.some((x) => x.naziv === prev) ? prev : k[0].naziv))
        if (o.length) setOpcina((prev) => (o.some((x) => x.naziv === prev) ? prev : o[0].naziv))
      })
      .catch(() => toast.error('Greška pri učitavanju podataka'))
  }, [open])

  const odabranaKvaliteta = useMemo(
    () => kvalitete.find((k) => k.naziv === kvalitetaNaziv),
    [kvalitete, kvalitetaNaziv],
  )

  const ukupnoBezPdv = useMemo(() => {
    if (!odabranaKvaliteta) return 0
    return odabranaKvaliteta.cijena * brojBrojeva
  }, [odabranaKvaliteta, brojBrojeva])

  const ukupnoSPdv = useMemo(() => ukupnoBezPdv * 1.17, [ukupnoBezPdv])

  const handleSubmit = async () => {
    if (!validirajJmbg(jmbg)) {
      toast.error('Neispravan JMBG')
      return
    }
    setLoading(true)
    try {
      const res = await api.dodijeliBulk({
        opcina_naziv: opcina,
        broj_brojeva: brojBrojeva,
        korisnik_ime: ime,
        korisnik_prezime: prezime,
        korisnik_jmbg: jmbg,
        korisnik_email: email,
        adresa,
        grad,
        postanski_broj: postanskiBroj,
        kvaliteta_naziv: kvalitetaNaziv,
        placanje: {
          nacin: nacinPlacanja,
          ...(nacinPlacanja === 'kartica'
            ? {
                broj_kartice: brojKartice,
                datum_isteka: datumIsteka,
                cvv,
                ime_vlasnika: imeVlasnika,
              }
            : {}),
        },
      })
      toast.success(
        `Dodijeljeno ${res.dodijeljeno} brojeva (${res.kvaliteta}) – ukupno ${res.ukupna_cijena.toFixed(2)} KM`,
      )
      if (res.email_poslan) toast.info('Zajednički račun poslan na email')
      setDokumenti(
        res.stavke.map((s) => ({
          msisdn_id: s.msisdn_id,
          broj_formatiran: s.broj_formatiran,
          racun_url: s.racun_url,
          ugovor_url: s.ugovor_url,
        })),
      )
      setSuccessOpen(true)
      onOpenChange(false)
      onSuccess?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Dialog
        open={open}
        onOpenChange={onOpenChange}
        title="Bulk dodjela"
        description="Zajednički podaci korisnika; po broju zaseban račun i ugovor za preuzimanje"
      >
        <span className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Općina"
            value={opcina}
            onValueChange={setOpcina}
            options={opcine.map((o) => ({
              value: o.naziv,
              label: `${o.naziv} (${(o.broj_msisdn ?? 0).toLocaleString('hr-HR')})`,
            }))}
          />
          <Input
            label="Broj komada"
            type="number"
            min={1}
            max={100}
            value={brojBrojeva}
            onChange={(e) => setBrojBrojeva(Number(e.target.value))}
          />
          <Select
            label="Kvaliteta brojeva"
            value={kvalitetaNaziv}
            onValueChange={setKvalitetaNaziv}
            options={kvalitete.map((k) => ({
              value: k.naziv,
              label: `${k.naziv.charAt(0).toUpperCase() + k.naziv.slice(1)} – ${k.cijena.toFixed(2)} KM/kom`,
            }))}
          />
          {odabranaKvaliteta && (
            <p className="sm:col-span-2 rounded-xl bg-[#F5F5F5] px-4 py-3 text-sm text-slate-700">
              {brojBrojeva} × {odabranaKvaliteta.cijena.toFixed(2)} KM ={' '}
              <strong>{ukupnoBezPdv.toFixed(2)} KM</strong> (bez PDV) · s PDV:{' '}
              <strong>{ukupnoSPdv.toFixed(2)} KM</strong>
            </p>
          )}
          <Input label="Ime" value={ime} onChange={(e) => setIme(e.target.value)} required />
          <Input label="Prezime" value={prezime} onChange={(e) => setPrezime(e.target.value)} required />
          <Input
            label="JMBG"
            value={jmbg}
            onChange={(e) => setJmbg(e.target.value.replace(/\D/g, '').slice(0, 13))}
            maxLength={13}
            required
          />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
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
        </span>
        <span className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Odustani
          </Button>
          <Button loading={loading} onClick={() => void handleSubmit()}>
            Dodijeli sve
          </Button>
        </span>
      </Dialog>

      <DodjelaSuccessModal
        open={successOpen}
        onOpenChange={setSuccessOpen}
        stavke={dokumenti}
        naslov="Bulk dodjela uspješna"
      />
    </>
  )
}
