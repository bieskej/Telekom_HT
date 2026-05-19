import * as Checkbox from '@radix-ui/react-checkbox'
import { Check, Download, FileText, ShieldAlert, Unlock } from 'lucide-react'
import { MsisdnUgovorResendButton } from '@/components/email/MsisdnUgovorResendButton'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { MsisdnItem } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { exportToCsv, formatStatus } from '@/lib/utils'

interface BrojeviTableProps {
  items: MsisdnItem[]
  selected: Set<number>
  onSelect: (id: number, checked: boolean) => void
  onSelectAll: (checked: boolean) => void
  zauzetiOnly: MsisdnItem[]
  mozeKarantena?: boolean
  onKarantena?: (id: number) => void
  onDetalj?: (id: number) => void
  isAdmin?: boolean
  onOslobodiKarantena?: (id: number) => void
  prikaziOslobodiKarantena?: boolean
}

export function BrojeviTable({
  items,
  selected,
  onSelect,
  onSelectAll,
  zauzetiOnly,
  mozeKarantena,
  onKarantena,
  onDetalj,
  isAdmin,
  onOslobodiKarantena,
  prikaziOslobodiKarantena,
}: BrojeviTableProps) {
  const handleExport = () => {
    exportToCsv(
      items.map((r) => ({
        broj: r.broj_formatiran,
        status: formatStatus(r.status),
        opcina: r.opcina_naziv ?? '',
        kvaliteta: r.kvaliteta ?? '',
        ime: r.ime ?? '',
        prezime: r.prezime ?? '',
        jmbg: r.jmbg ?? '',
      })),
      `eronet-brojevi-${new Date().toISOString().slice(0, 10)}.csv`,
    )
  }

  const allZauzetSelected =
    zauzetiOnly.length > 0 && zauzetiOnly.every((r) => selected.has(r.id))

  return (
    <span className="block space-y-4">
      <span className="flex justify-end">
        <Button variant="outline" size="sm" onClick={handleExport} disabled={!items.length}>
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </span>

      <Card className="hidden overflow-hidden md:block">
        <span className="block overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 bg-[#F5F5F5]/80">
              <tr>
                <th className="w-10 p-4">
                  <Checkbox.Root
                    checked={allZauzetSelected}
                    onCheckedChange={(c) => onSelectAll(!!c)}
                    className="flex h-5 w-5 items-center justify-center rounded border border-slate-300 data-[state=checked]:border-[#0054A6] data-[state=checked]:bg-[#0054A6]"
                  >
                    <Checkbox.Indicator>
                      <Check className="h-3 w-3 text-white" />
                    </Checkbox.Indicator>
                  </Checkbox.Root>
                </th>
                <th className="p-4 font-semibold text-slate-700">Broj</th>
                <th className="p-4 font-semibold text-slate-700">Status</th>
                <th className="p-4 font-semibold text-slate-700">Općina</th>
                <th className="p-4 font-semibold text-slate-700">Kvaliteta</th>
                <th className="p-4 font-semibold text-slate-700">Korisnik</th>
                <th className="p-4 font-semibold text-slate-700">Dokumenti</th>
                {mozeKarantena && <th className="p-4 font-semibold text-slate-700">Karantena</th>}
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer border-b border-slate-50 transition hover:bg-[#0054A6]/4"
                  onClick={() => onDetalj?.(row.id)}
                >
                  <td className="p-4" onClick={(e) => e.stopPropagation()}>
                    {row.status === 'zauzet' && (
                      <Checkbox.Root
                        checked={selected.has(row.id)}
                        onCheckedChange={(c) => onSelect(row.id, !!c)}
                        className="flex h-5 w-5 items-center justify-center rounded border border-slate-300 data-[state=checked]:border-[#0054A6] data-[state=checked]:bg-[#0054A6]"
                      >
                        <Checkbox.Indicator>
                          <Check className="h-3 w-3 text-white" />
                        </Checkbox.Indicator>
                      </Checkbox.Root>
                    )}
                  </td>
                  <td className="p-4 font-mono font-medium text-[#0054A6]">{row.broj_formatiran}</td>
                  <td className="p-4">
                    <Badge variant={row.status as 'slobodan' | 'zauzet' | 'karantena'}>
                      {formatStatus(row.status)}
                    </Badge>
                  </td>
                  <td className="p-4 text-slate-600">{row.opcina_naziv ?? '—'}</td>
                  <td className="p-4 capitalize text-slate-600">
                    {row.kvaliteta_naziv ?? row.kvaliteta ?? '—'}
                  </td>
                  <td className="p-4 text-slate-600">
                    {row.ime ? `${row.ime} ${row.prezime}` : '—'}
                  </td>
                  <td className="p-4" onClick={(e) => e.stopPropagation()}>
                    {row.status === 'zauzet' && (
                      <span className="flex flex-wrap gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            api.preuzmiRacun(row.id).catch((e) =>
                              toast.error(e instanceof Error ? e.message : 'Greška'),
                            )
                          }
                        >
                          <Download className="h-3.5 w-3.5" />
                          Račun
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            api.preuzmiUgovor(row.id).catch((e) =>
                              toast.error(e instanceof Error ? e.message : 'Greška'),
                            )
                          }
                        >
                          <FileText className="h-3.5 w-3.5" />
                          Ugovor
                        </Button>
                        <MsisdnUgovorResendButton msisdnId={row.id} />
                      </span>
                    )}
                    {prikaziOslobodiKarantena && row.status === 'karantena' && isAdmin && onOslobodiKarantena && (
                      <Button variant="accent" size="sm" onClick={() => onOslobodiKarantena(row.id)}>
                        <Unlock className="h-3.5 w-3.5" />
                        Oslobodi
                      </Button>
                    )}
                  </td>
                  {mozeKarantena && (
                    <td className="p-4" onClick={(e) => e.stopPropagation()}>
                      {row.status === 'zauzet' && onKarantena && (
                        <Button variant="outline" size="sm" onClick={() => onKarantena(row.id)}>
                          <ShieldAlert className="h-3.5 w-3.5" />
                          Stavi u karantenu
                        </Button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </span>
      </Card>

      <span className="block space-y-3 md:hidden">
        {items.map((row) => (
          <Card key={row.id} className="p-4 card-hover">
            <span className="flex items-start justify-between gap-2">
              <span className="flex items-start gap-3">
                {row.status === 'zauzet' && (
                  <Checkbox.Root
                    checked={selected.has(row.id)}
                    onCheckedChange={(c) => onSelect(row.id, !!c)}
                    className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded border border-slate-300 data-[state=checked]:border-[#0054A6] data-[state=checked]:bg-[#0054A6]"
                  >
                    <Checkbox.Indicator>
                      <Check className="h-3 w-3 text-white" />
                    </Checkbox.Indicator>
                  </Checkbox.Root>
                )}
                <span>
                  <p className="font-mono text-base font-semibold text-[#0054A6]">{row.broj_formatiran}</p>
                  <p className="mt-1 text-sm text-slate-500">{row.opcina_naziv ?? '—'}</p>
                </span>
              </span>
              <Badge variant={row.status as 'slobodan' | 'zauzet' | 'karantena'}>
                {formatStatus(row.status)}
              </Badge>
            </span>
            {(row.ime || row.kvaliteta) && (
              <p className="mt-3 border-t border-slate-100 pt-3 text-sm text-slate-600">
                {row.ime && `${row.ime} ${row.prezime}`}
                {row.kvaliteta && ` · ${row.kvaliteta}`}
              </p>
            )}
            {row.status === 'zauzet' && (
              <span className="mt-3 flex flex-col gap-2 border-t border-slate-100 pt-3">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() =>
                    api.preuzmiRacun(row.id).catch((e) =>
                      toast.error(e instanceof Error ? e.message : 'Greška'),
                    )
                  }
                >
                  <Download className="h-4 w-4" />
                  Preuzmi račun
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() =>
                    api.preuzmiUgovor(row.id).catch((e) =>
                      toast.error(e instanceof Error ? e.message : 'Greška'),
                    )
                  }
                >
                  <FileText className="h-4 w-4" />
                  Preuzmi ugovor
                </Button>
                <MsisdnUgovorResendButton msisdnId={row.id} className="w-full" />
                {mozeKarantena && onKarantena && (
                  <Button variant="outline" size="sm" className="w-full" onClick={() => onKarantena(row.id)}>
                    <ShieldAlert className="h-4 w-4" />
                    Stavi u karantenu
                  </Button>
                )}
              </span>
            )}
          </Card>
        ))}
      </span>
    </span>
  )
}
