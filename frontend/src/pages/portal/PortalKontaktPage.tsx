import { useState } from 'react'
import { toast } from 'sonner'
import { mapApiError } from '@/lib/api'
import { portalApi } from '@/lib/portalApi'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
const textareaClass =
  'w-full rounded-[10px] border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 transition-colors placeholder:text-slate-400 focus:border-[#00A3E0] focus:outline-none focus:ring-2 focus:ring-[#00A3E0]/25 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500'

export function PortalKontaktPage() {
  const [predmet, setPredmet] = useState('')
  const [poruka, setPoruka] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await portalApi.kontakt(predmet, poruka)
      toast.success(res.poruka)
      setPredmet('')
      setPoruka('')
    } catch (err) {
      toast.error(mapApiError(err, 'Slanje nije uspjelo.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kontakt</CardTitle>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Pošaljite upit HT Eronet podršci. Odgovor stiže na email s vašeg računa.
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
          <Input
            label="Predmet"
            value={predmet}
            onChange={(e) => setPredmet(e.target.value)}
            required
          />
          <div className="space-y-1.5">
            <label htmlFor="portal-kontakt-poruka" className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Poruka
            </label>
            <textarea
              id="portal-kontakt-poruka"
              value={poruka}
              onChange={(e) => setPoruka(e.target.value)}
              rows={6}
              required
              className={textareaClass}
            />
          </div>
          <Button type="submit" loading={loading}>
            Pošalji poruku
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
