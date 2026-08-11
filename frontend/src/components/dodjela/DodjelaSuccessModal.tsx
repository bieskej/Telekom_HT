import { Download, FileText } from 'lucide-react'
import { api } from '@/lib/api'
import { MsisdnUgovorResendButton } from '@/components/email/MsisdnUgovorResendButton'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'

export interface DodjelaDokumentStavka {
  msisdn_id: number
  broj_formatiran?: string
  racun_url: string
  ugovor_url: string
}

interface DodjelaSuccessModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  stavke: DodjelaDokumentStavka[]
  naslov?: string
}

export function DodjelaSuccessModal({
  open,
  onOpenChange,
  stavke,
  naslov = 'Dodjela uspješna',
}: DodjelaSuccessModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={naslov}
      description="Preuzmite račun i ugovor za dodijeljene brojeve. Ugovor se ne šalje emailom."
    >
      <ul className="max-h-80 space-y-4 overflow-y-auto">
        {stavke.map((s) => (
          <li key={s.msisdn_id} className="rounded-xl border border-slate-100 bg-slate-50/80 p-4">
            {s.broj_formatiran && (
              <p className="mb-3 font-mono text-sm font-semibold text-[#0054A6]">{s.broj_formatiran}</p>
            )}
            <span className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => void api.preuzmiRacun(s.msisdn_id)}
              >
                <Download className="h-4 w-4" />
                Preuzmi račun
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void api.preuzmiUgovor(s.msisdn_id)}
              >
                <FileText className="h-4 w-4" />
                Preuzmi ugovor
              </Button>
              <MsisdnUgovorResendButton msisdnId={s.msisdn_id} />
            </span>
          </li>
        ))}
      </ul>
    </Dialog>
  )
}
