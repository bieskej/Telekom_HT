import { Download } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { mapApiError } from '@/lib/api'
import { portalApi } from '@/lib/portalApi'
import type { KupacMsisdnItem } from '@/types/api'
import { MsisdnStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/TableSkeleton'

export function PortalMojiBrojeviPage() {
  const [brojevi, setBrojevi] = useState<KupacMsisdnItem[]>([])
  const [ukupno, setUkupno] = useState(0)
  const [stranica, setStranica] = useState(1)
  const [loading, setLoading] = useState(true)
  const [preuzimanjeId, setPreuzimanjeId] = useState<number | null>(null)

  const ucitaj = useCallback(async (s: number) => {
    setLoading(true)
    try {
      const res = await portalApi.mojiBrojevi(s)
      setBrojevi(res.brojevi)
      setUkupno(res.ukupno)
      setStranica(res.stranica)
    } catch (e) {
      toast.error(mapApiError(e, 'Brojevi nisu učitani.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    ucitaj(1)
  }, [ucitaj])

  const preuzmiUgovor = async (id: number) => {
    setPreuzimanjeId(id)
    try {
      await portalApi.preuzmiUgovor(id)
      toast.success('Ugovor preuzet')
    } catch (e) {
      toast.error(mapApiError(e, 'Preuzimanje nije uspjelo.'))
    } finally {
      setPreuzimanjeId(null)
    }
  }

  const ukupnoStranica = Math.max(1, Math.ceil(ukupno / 20))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Moji brojevi</CardTitle>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Brojevi povezani s vašim JMBG-om ({ukupno} ukupno)
        </p>
      </CardHeader>
      <CardContent>
        {loading ? (
          <TableSkeleton rows={4} />
        ) : brojevi.length === 0 ? (
          <EmptyState
            title="Nemate dodijeljenih brojeva"
            description="Nakon dodjele i aktivacije ugovora u poslovnici HT Eronet, brojevi će se pojaviti na ovom popisu. Za upit kontaktirajte podršku."
            action={{ label: 'Kontakt podršci', to: '/portal/kontakt' }}
            className="border-0 shadow-none"
          />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-100 dark:border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-600 dark:bg-slate-800/80 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">Broj</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Kvaliteta</th>
                  <th className="px-3 py-2">Datum dodjele</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {brojevi.map((b) => (
                  <tr
                    key={b.id}
                    className="border-t border-slate-100 dark:border-slate-800"
                  >
                    <td className="px-3 py-2 font-mono text-[#0054A6] dark:text-[#00A3E0]">
                      {b.broj}
                    </td>
                    <td className="px-3 py-2">
                      <MsisdnStatusBadge status={b.status} />
                    </td>
                    <td className="px-3 py-2 capitalize text-slate-700 dark:text-slate-300">
                      {b.kvaliteta ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-slate-600 dark:text-slate-400">
                      {b.datum_dodjele
                        ? new Date(b.datum_dodjele).toLocaleDateString('hr-HR')
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        loading={preuzimanjeId === b.id}
                        onClick={() => preuzmiUgovor(b.id)}
                      >
                        <Download className="mr-1 h-3.5 w-3.5" />
                        Preuzmi ugovor
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {ukupnoStranica > 1 && (
          <div className="mt-4 flex items-center justify-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={stranica <= 1}
              onClick={() => ucitaj(stranica - 1)}
            >
              Prethodna
            </Button>
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {stranica} / {ukupnoStranica}
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={stranica >= ukupnoStranica}
              onClick={() => ucitaj(stranica + 1)}
            >
              Sljedeća
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
