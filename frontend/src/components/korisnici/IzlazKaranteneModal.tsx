import { useState } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'

interface IzlazKaranteneModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  msisdnId: number | null
  brojFormatiran?: string
  isAdmin: boolean
  onSuccess?: () => void
}

export function IzlazKaranteneModal({
  open,
  onOpenChange,
  msisdnId,
  brojFormatiran,
  isAdmin,
  onSuccess,
}: IzlazKaranteneModalProps) {
  const [razlog, setRazlog] = useState('')
  const [loading, setLoading] = useState<'aktivno' | 'slobodan' | null>(null)

  const handleVratiAktivno = async () => {
    if (msisdnId == null) return
    setLoading('aktivno')
    try {
      await api.vratiIzKaranteneAktivno(msisdnId, razlog.trim() || undefined)
      toast.success('Broj je vraćen u aktivno stanje.')
      onOpenChange(false)
      setRazlog('')
      onSuccess?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    } finally {
      setLoading(null)
    }
  }

  const handleOslobodi = async () => {
    if (msisdnId == null) return
    setLoading('slobodan')
    try {
      await api.oslobodiIzKarantene(msisdnId, razlog.trim() || undefined)
      toast.success('Broj je oslobođen u inventar slobodnih brojeva.')
      onOpenChange(false)
      setRazlog('')
      onSuccess?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    } finally {
      setLoading(null)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Izlaz iz karantene"
      description={brojFormatiran ? `Broj: ${brojFormatiran}` : 'Odaberite način izlaska iz karantene'}
    >
      <div className="space-y-4">
        <p className="text-sm text-slate-600">
          <strong>Vrati u aktivno</strong> — broj ostaje dodijeljen korisniku.
          {isAdmin && (
            <>
              {' '}
              <strong>Oslobodi broj</strong> — briše podatke kupca i vraća broj u slobodan inventar.
            </>
          )}
        </p>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Razlog (opcionalno)</label>
          <textarea
            value={razlog}
            onChange={(e) => setRazlog(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-[#00A3E0] focus:ring-1 focus:ring-[#00A3E0]"
          />
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Odustani
          </Button>
          <Button loading={loading === 'aktivno'} onClick={() => void handleVratiAktivno()}>
            Vrati u aktivno
          </Button>
          {isAdmin && (
            <Button
              variant="danger"
              loading={loading === 'slobodan'}
              onClick={() => void handleOslobodi()}
            >
              Oslobodi broj
            </Button>
          )}
        </div>
      </div>
    </Dialog>
  )
}
