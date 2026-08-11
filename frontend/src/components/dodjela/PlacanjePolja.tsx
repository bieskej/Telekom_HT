import { Input } from '@/components/ui/Input'

export type NacinPlacanja = 'gotovina' | 'kartica'

interface PlacanjePoljaProps {
  nacin: NacinPlacanja
  onNacinChange: (v: NacinPlacanja) => void
  brojKartice: string
  onBrojKarticeChange: (v: string) => void
  datumIsteka: string
  onDatumIstekaChange: (v: string) => void
  cvv: string
  onCvvChange: (v: string) => void
  imeVlasnika: string
  onImeVlasnikaChange: (v: string) => void
}

export function PlacanjePolja({
  nacin,
  onNacinChange,
  brojKartice,
  onBrojKarticeChange,
  datumIsteka,
  onDatumIstekaChange,
  cvv,
  onCvvChange,
  imeVlasnika,
  onImeVlasnikaChange,
}: PlacanjePoljaProps) {
  return (
    <fieldset className="lg:col-span-2 space-y-4 rounded-xl border border-slate-200 p-4">
      <legend className="px-1 text-sm font-semibold text-slate-700">Način plaćanja</legend>
      <span className="flex flex-wrap gap-6">
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="radio"
            name="nacin_placanja"
            checked={nacin === 'gotovina'}
            onChange={() => onNacinChange('gotovina')}
            className="text-[#0054A6]"
          />
          Gotovina
        </label>
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="radio"
            name="nacin_placanja"
            checked={nacin === 'kartica'}
            onChange={() => onNacinChange('kartica')}
            className="text-[#0054A6]"
          />
          Kartica
        </label>
      </span>
      {nacin === 'kartica' && (
        <span className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Broj kartice"
            value={brojKartice}
            onChange={(e) => onBrojKarticeChange(e.target.value.replace(/\D/g, '').slice(0, 16))}
            placeholder="16 znamenki"
            maxLength={16}
            required
          />
          <Input
            label="Datum isteka (MM/GG)"
            value={datumIsteka}
            onChange={(e) => {
              let v = e.target.value.replace(/[^\d/]/g, '')
              if (v.length === 2 && !v.includes('/') && datumIsteka.length < v.length) v += '/'
              onDatumIstekaChange(v.slice(0, 5))
            }}
            placeholder="MM/GG"
            maxLength={5}
            required
          />
          <Input
            label="CVV"
            value={cvv}
            onChange={(e) => onCvvChange(e.target.value.replace(/\D/g, '').slice(0, 3))}
            maxLength={3}
            required
          />
          <Input
            label="Ime vlasnika kartice"
            value={imeVlasnika}
            onChange={(e) => onImeVlasnikaChange(e.target.value)}
            required
          />
        </span>
      )}
    </fieldset>
  )
}
