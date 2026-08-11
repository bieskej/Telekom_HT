import { Mail } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'

interface MsisdnUgovorResendButtonProps {
  msisdnId: number
  size?: 'sm' | 'md'
  className?: string
}

/** Pronalazi zadnji email log za MSISDN i ponavlja slanje (ugovor/dodjela). */
export function MsisdnUgovorResendButton({
  msisdnId,
  size = 'sm',
  className,
}: MsisdnUgovorResendButtonProps) {
  const [loading, setLoading] = useState(false)

  const handleResend = async () => {
    setLoading(true)
    try {
      const lista = await api.emailLogList({ msisdn_id: msisdnId, limit: 1 })
      const log = lista.stavke.find((s) => s.ima_html)
      if (!log) {
        toast.error('Nema pohranjenog emaila za ovaj broj.')
        return
      }
      await api.emailResend(log.id)
      toast.success('Ugovor je ponovno poslan na email kupca.')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Ponovno slanje nije uspjelo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      variant="outline"
      size={size}
      className={className}
      disabled={loading}
      onClick={() => void handleResend()}
    >
      <Mail className="h-4 w-4" />
      {loading ? 'Šaljem…' : 'Pošalji ugovor ponovno'}
    </Button>
  )
}
