import { useEffect, useState } from 'react'
import { ShieldAlert, Unlock } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import type { MsisdnDetalj } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { Input } from '@/components/ui/Input'
import { MsisdnUgovorResendButton } from '@/components/email/MsisdnUgovorResendButton'
import { formatStatus } from '@/lib/utils'

interface MsisdnDetaljModalProps {
  msisdnId: number | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpdated?: () => void
}

export function MsisdnDetaljModal({
  msisdnId,
  open,
  onOpenChange,
  onUpdated,
}: MsisdnDetaljModalProps) {
  const { hasUloga } = useAuth()
  const isAdmin = hasUloga('admin')
  const mozeKarantena = hasUloga('admin', 'prodaja')

  const [detalj, setDetalj] = useState<MsisdnDetalj | null>(null)
  const [loading, setLoading] = useState(false)
  const [dana, setDana] = useState(30)
  const [razlog, setRazlog] = useState('')
  const [confirmAction, setConfirmAction] = useState<'produzi' | 'skrati' | 'oslobodi' | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open || !msisdnId) {
      setDetalj(null)
      return
    }
    setLoading(true)
    api
      .msisdnDetalj(msisdnId)
      .then((d) => {
        setDetalj(d)
        setDana(d.karantena_dana ?? 30)
        setRazlog(d.karantena_razlog ?? '')
      })
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Greška'))
      .finally(() => setLoading(false))
  }, [open, msisdnId])

  const runAction = async () => {
    if (!msisdnId || !confirmAction) return
    setSubmitting(true)
    try {
      if (confirmAction === 'produzi') {
        await api.patchKarantena(msisdnId, { produzi_dana: dana, razlog: razlog || undefined })
        toast.success('Karantena je produžena.')
      } else if (confirmAction === 'skrati') {
        await api.patchKarantena(msisdnId, { skrati_dana: dana, razlog: razlog || undefined })
        toast.success('Karantena je skraćena.')
      } else {
        await api.oslobodiIzKarantene(msisdnId, razlog || undefined)
        toast.success('Broj je oslobođen iz karantene.')
        onOpenChange(false)
      }
      setConfirmAction(null)
      onUpdated?.()
      if (confirmAction !== 'oslobodi' && msisdnId) {
        const d = await api.msisdnDetalj(msisdnId)
        setDetalj(d)
        setDana(d.karantena_dana ?? dana)
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Akcija nije uspjela.')
    } finally {
      setSubmitting(false)
    }
  }

  const istekLabel =
    detalj?.datum_isteka &&
    new Date(detalj.datum_isteka).toLocaleDateString('hr-HR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })

  return (
    <>
      <Dialog
        open={open}
        onOpenChange={onOpenChange}
        title={detalj ? detalj.broj_formatiran : 'Detalj broja'}
        description={detalj ? `${detalj.opcina_naziv ?? '—'} · ${formatStatus(detalj.status)}` : undefined}
        className="max-w-lg"
      >
        {loading && <p className="text-sm text-slate-500">Učitavanje…</p>}
        {detalj && !loading && (
          <span className="block space-y-4">
            <span className="flex flex-wrap items-center gap-2">
              <Badge variant={detalj.status as 'slobodan' | 'zauzet' | 'karantena'}>
                {formatStatus(detalj.status)}
              </Badge>
              {detalj.kvaliteta && (
                <span className="text-sm capitalize text-slate-600">{detalj.kvaliteta}</span>
              )}
            </span>
            {(detalj.ime || detalj.email) && (
              <dl className="grid gap-1 text-sm">
                {detalj.ime && (
                  <div>
                    <dt className="text-slate-500">Korisnik</dt>
                    <dd>
                      {detalj.ime} {detalj.prezime}
                    </dd>
                  </div>
                )}
                {detalj.email && (
                  <div>
                    <dt className="text-slate-500">Email</dt>
                    <dd>{detalj.email}</dd>
                  </div>
                )}
              </dl>
            )}
            {detalj.status === 'zauzet' && <MsisdnUgovorResendButton msisdnId={detalj.id} />}
            {detalj.status === 'karantena' && mozeKarantena && (
              <KarantenaSekcija
                detalj={detalj}
                istekLabel={istekLabel}
                dana={dana}
                setDana={setDana}
                razlog={razlog}
                setRazlog={setRazlog}
                isAdmin={isAdmin}
                onProduzi={() => setConfirmAction('produzi')}
                onSkrati={() => setConfirmAction('skrati')}
                onOslobodi={() => setConfirmAction('oslobodi')}
              />
            )}
          </span>
        )}
      </Dialog>

      <Dialog
        open={confirmAction !== null}
        onOpenChange={(o) => !o && setConfirmAction(null)}
        title={
          confirmAction === 'oslobodi'
            ? 'Osloboditi broj iz karantene?'
            : confirmAction === 'skrati'
              ? 'Skratiti karantenu?'
              : 'Produžiti karantenu?'
        }
        description={
          confirmAction === 'oslobodi'
            ? 'Broj će postati slobodan i podaci kupca bit će uklonjeni.'
            : `Promjena za ${dana} dan(a).`
        }
      >
        <span className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setConfirmAction(null)} disabled={submitting}>
            Odustani
          </Button>
          <Button variant="accent" onClick={() => void runAction()} disabled={submitting}>
            Potvrdi
          </Button>
        </span>
      </Dialog>
    </>
  )
}

function KarantenaSekcija({
  detalj,
  istekLabel,
  dana,
  setDana,
  razlog,
  setRazlog,
  isAdmin,
  onProduzi,
  onSkrati,
  onOslobodi,
}: {
  detalj: MsisdnDetalj
  istekLabel: string | false
  dana: number
  setDana: (n: number) => void
  razlog: string
  setRazlog: (s: string) => void
  isAdmin: boolean
  onProduzi: () => void
  onSkrati: () => void
  onOslobodi: () => void
}) {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4">
      <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-900">
        <ShieldAlert className="h-4 w-4" />
        Karantena
      </p>
      <p className="mb-3 text-xs text-amber-800">
        Trajanje: {detalj.karantena_dana} dana
        {istekLabel ? ` · istječe ${istekLabel}` : ''}
      </p>
      <label className="mb-1 block text-xs font-medium text-slate-600">
        Dani za akciju (1–180): {dana}
      </label>
      <input
        type="range"
        min={1}
        max={180}
        value={dana}
        onChange={(e) => setDana(Number(e.target.value))}
        className="mb-3 w-full accent-[#0054A6]"
      />
      <Input
        label="Razlog (opcionalno)"
        value={razlog}
        onChange={(e) => setRazlog(e.target.value)}
        placeholder="npr. zahtjev kupca"
      />
      <span className="mt-4 flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={onProduzi}>
          Produži
        </Button>
        {isAdmin && (
          <Button variant="outline" size="sm" onClick={onSkrati}>
            Skrati
          </Button>
        )}
        {isAdmin && (
          <Button variant="accent" size="sm" onClick={onOslobodi}>
            <Unlock className="h-4 w-4" />
            Oslobodi
          </Button>
        )}
      </span>
    </div>
  )
}
