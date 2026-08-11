import * as Slider from '@radix-ui/react-slider'
import { useState } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'

interface ProduziKarantenuModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  msisdnId: number | null
  brojFormatiran?: string
  onSuccess?: () => void
}

export function ProduziKarantenuModal({
  open,
  onOpenChange,
  msisdnId,
  brojFormatiran,
  onSuccess,
}: ProduziKarantenuModalProps) {
  const [dana, setDana] = useState(30)
  const [razlog, setRazlog] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (msisdnId == null) return
    setLoading(true)
    try {
      await api.patchKarantena(msisdnId, {
        produzi_dana: dana,
        razlog: razlog.trim() || undefined,
      })
      toast.success('Karantena je produžena.')
      onOpenChange(false)
      setRazlog('')
      onSuccess?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška pri produženju karantene')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Produži karantenu"
      description={brojFormatiran ? `Broj: ${brojFormatiran}` : 'Dodaj dane trajanja karantene'}
    >
      <div className="space-y-4">
        <div>
          <label className="mb-3 block text-sm font-medium text-slate-700">
            Produži za (dana): <span className="text-[#0054A6]">{dana}</span>
          </label>
          <Slider.Root
            className="relative flex h-5 w-full touch-none items-center"
            value={[dana]}
            onValueChange={([v]) => setDana(v)}
            min={1}
            max={180}
            step={1}
          >
            <Slider.Track className="relative h-2 grow rounded-full bg-slate-200">
              <Slider.Range className="absolute h-full rounded-full bg-[#0054A6]" />
            </Slider.Track>
            <Slider.Thumb className="block h-5 w-5 rounded-full border-2 border-[#0054A6] bg-white shadow-md focus:outline-none focus:ring-2 focus:ring-[#00A3E0]" />
          </Slider.Root>
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-700">Razlog (opcionalno)</label>
          <textarea
            value={razlog}
            onChange={(e) => setRazlog(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-[#00A3E0] focus:ring-1 focus:ring-[#00A3E0]"
            placeholder="Npr. korisnik tražio produženje"
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Odustani
          </Button>
          <Button loading={loading} onClick={() => void handleSubmit()}>
            Produži
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
