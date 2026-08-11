import * as Slider from '@radix-ui/react-slider'
import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { toast } from 'sonner'

interface OslobodiModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  msisdnIds: number[]
  onSuccess?: () => void
  title?: string
  confirmLabel?: string
}

export function OslobodiModal({
  open,
  onOpenChange,
  msisdnIds,
  onSuccess,
  title = 'Stavi u karantenu',
  confirmLabel = 'Stavi u karantenu',
}: OslobodiModalProps) {
  const [dana, setDana] = useState(60)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!msisdnIds.length) return
    setLoading(true)
    try {
      for (const id of msisdnIds) {
        await api.oslobodi(id, dana)
      }
      toast.success(
        msisdnIds.length === 1
          ? 'Broj je stavljen u karantenu'
          : `${msisdnIds.length} brojeva stavljeno u karantenu`,
      )
      onOpenChange(false)
      onSuccess?.()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška pri oslobađanju')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={
        msisdnIds.length > 1
          ? `Odabrano ${msisdnIds.length} brojeva za karantenu`
          : 'Postavite trajanje karantene u danima'
      }
    >
      <div className="space-y-6">
        <div>
          <label className="mb-3 block text-sm font-medium text-slate-700">
            Karantena (dana): <span className="text-[#0054A6]">{dana}</span>
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
          <p className="mt-2 text-xs text-slate-500">Zadano: 60 dana</p>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Odustani
          </Button>
          <Button variant="danger" loading={loading} onClick={() => void handleSubmit()}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
