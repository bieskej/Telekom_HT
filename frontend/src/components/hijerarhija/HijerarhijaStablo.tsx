import { ChevronDown, ChevronRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { cn } from '@/lib/utils'
import type {
  HijerarhijaCvorTip,
  HijerarhijaStabloLokacija,
  HijerarhijaStabloOpcina,
  HijerarhijaStabloZupanija,
} from '@/types/api'

export interface OdabraniCvor {
  tip: HijerarhijaCvorTip
  id: number
}

interface HijerarhijaStabloProps {
  stablo: HijerarhijaStabloZupanija[]
  pretraga: string
  odabrani: OdabraniCvor | null
  onOdabir: (cvor: OdabraniCvor) => void
}

function Badge({ count }: { count: number }) {
  return (
    <span className="ml-auto shrink-0 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
      {count.toLocaleString('hr-HR')}
    </span>
  )
}

function filtriraj(
  stablo: HijerarhijaStabloZupanija[],
  q: string,
): HijerarhijaStabloZupanija[] {
  const query = q.trim().toLowerCase()
  if (!query) return stablo
  const result: HijerarhijaStabloZupanija[] = []
  for (const z of stablo) {
    const opcine: HijerarhijaStabloOpcina[] = []
    for (const o of z.opcine ?? []) {
      const lokacije: HijerarhijaStabloLokacija[] = []
      for (const l of o.lokacije ?? []) {
        const uredjajiMatch = (l.uredjaji ?? []).filter((u) =>
          (u.naziv ?? '').toLowerCase().includes(query),
        )
        const lokMatch =
          l.naziv.toLowerCase().includes(query) || uredjajiMatch.length > 0
        if (lokMatch) {
          lokacije.push({
            ...l,
            uredjaji: uredjajiMatch.length > 0 ? uredjajiMatch : l.uredjaji,
          })
        }
      }
      const opMatch =
        o.naziv.toLowerCase().includes(query) || lokacije.length > 0
      if (opMatch) {
        opcine.push({
          ...o,
          lokacije: lokacije.length > 0 ? lokacije : o.lokacije,
        })
      }
    }
    const zMatch =
      z.naziv.toLowerCase().includes(query) ||
      z.oznaka.toLowerCase().includes(query) ||
      opcine.length > 0
    if (zMatch) {
      result.push({
        ...z,
        opcine: opcine.length > 0 ? opcine : z.opcine,
      })
    }
  }
  return result
}

export function HijerarhijaStablo({
  stablo,
  pretraga,
  odabrani,
  onOdabir,
}: HijerarhijaStabloProps) {
  const [expZ, setExpZ] = useState<Set<number>>(new Set())
  const [expO, setExpO] = useState<Set<number>>(new Set())
  const [expL, setExpL] = useState<Set<number>>(new Set())

  const filtrirano = useMemo(() => filtriraj(stablo, pretraga), [stablo, pretraga])

  useEffect(() => {
    if (!pretraga.trim()) return
    const z = new Set<number>()
    const o = new Set<number>()
    const l = new Set<number>()
    filtrirano.forEach((zup) => {
      z.add(zup.id)
      zup.opcine.forEach((op) => {
        o.add(op.id)
        op.lokacije.forEach((lok) => l.add(lok.id))
      })
    })
    setExpZ(z)
    setExpO(o)
    setExpL(l)
  }, [pretraga, filtrirano])

  useEffect(() => {
    if (!odabrani || !stablo.length) return
    for (const z of stablo) {
      if (odabrani.tip === 'zupanija' && z.id === odabrani.id) {
        setExpZ((prev) => new Set(prev).add(z.id))
        return
      }
      for (const o of z.opcine ?? []) {
        if (odabrani.tip === 'opcina' && o.id === odabrani.id) {
          setExpZ((prev) => new Set(prev).add(z.id))
          setExpO((prev) => new Set(prev).add(o.id))
          return
        }
        for (const l of o.lokacije ?? []) {
          if (odabrani.tip === 'lokacija' && l.id === odabrani.id) {
            setExpZ((prev) => new Set(prev).add(z.id))
            setExpO((prev) => new Set(prev).add(o.id))
            setExpL((prev) => new Set(prev).add(l.id))
            return
          }
          for (const u of l.uredjaji ?? []) {
            if (odabrani.tip === 'uredjaj' && u.id === odabrani.id) {
              setExpZ((prev) => new Set(prev).add(z.id))
              setExpO((prev) => new Set(prev).add(o.id))
              setExpL((prev) => new Set(prev).add(l.id))
              return
            }
          }
        }
      }
    }
  }, [odabrani, stablo])

  const toggle = (
    set: Set<number>,
    setter: (s: Set<number>) => void,
    id: number,
  ) => {
    const next = new Set(set)
    next.has(id) ? next.delete(id) : next.add(id)
    setter(next)
  }

  const isOdabran = (tip: HijerarhijaCvorTip, id: number) =>
    odabrani?.tip === tip && odabrani.id === id

  if (filtrirano.length === 0) {
    return <p className="px-2 py-4 text-sm text-slate-400">Nema rezultata.</p>
  }

  return (
    <div className="space-y-0.5 text-sm">
      {filtrirano.map((z) => (
        <div key={z.id}>
          <div
            className={cn(
              'flex items-center gap-1 rounded-lg pr-2 hover:bg-[#0054A6]/8',
              isOdabran('zupanija', z.id) && 'bg-[#0054A6] text-white hover:bg-[#0054A6]',
            )}
          >
            <button
              type="button"
              onClick={() => toggle(expZ, setExpZ, z.id)}
              className="px-1 py-1.5"
              aria-label={expZ.has(z.id) ? 'Sakrij' : 'Prikaži'}
            >
              {expZ.has(z.id) ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            <button
              type="button"
              onClick={() => onOdabir({ tip: 'zupanija', id: z.id })}
              className="flex flex-1 items-center gap-2 py-1.5 text-left font-semibold"
            >
              <span className="truncate">{z.naziv}</span>
              <span
                className={cn(
                  'text-[10px]',
                  isOdabran('zupanija', z.id) ? 'opacity-80' : 'text-slate-400',
                )}
              >
                ({z.oznaka})
              </span>
              <Badge count={z.ukupno} />
            </button>
          </div>

          {expZ.has(z.id) &&
            z.opcine.map((o) => (
              <div key={o.id} className="ml-4 border-l border-slate-100 pl-1">
                <div
                  className={cn(
                    'flex items-center gap-1 rounded pr-2 hover:bg-slate-50',
                    isOdabran('opcina', o.id) && 'bg-[#0054A6] text-white hover:bg-[#0054A6]',
                  )}
                >
                  <button
                    type="button"
                    onClick={() => toggle(expO, setExpO, o.id)}
                    className="px-1 py-1"
                    aria-label={expO.has(o.id) ? 'Sakrij' : 'Prikaži'}
                  >
                    {expO.has(o.id) ? (
                      <ChevronDown className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => onOdabir({ tip: 'opcina', id: o.id })}
                    className="flex flex-1 items-center gap-2 py-1 text-left text-xs font-medium"
                  >
                    <span className="truncate">{o.naziv}</span>
                    <Badge count={o.ukupno} />
                  </button>
                </div>

                {expO.has(o.id) &&
                  o.lokacije.map((l) => (
                    <div key={l.id} className="ml-4 border-l border-slate-50 pl-1">
                      <div
                        className={cn(
                          'flex items-center gap-1 rounded pr-2 hover:bg-slate-50',
                          isOdabran('lokacija', l.id) &&
                            'bg-[#0054A6] text-white hover:bg-[#0054A6]',
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => toggle(expL, setExpL, l.id)}
                          className="px-1 py-1"
                          aria-label={expL.has(l.id) ? 'Sakrij' : 'Prikaži'}
                        >
                          {expL.has(l.id) ? (
                            <ChevronDown className="h-3 w-3" />
                          ) : (
                            <ChevronRight className="h-3 w-3" />
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => onOdabir({ tip: 'lokacija', id: l.id })}
                          className="flex flex-1 items-center gap-2 py-1 text-left text-xs"
                        >
                          <span className="truncate">{l.naziv}</span>
                          <Badge count={l.ukupno} />
                        </button>
                      </div>

                      {expL.has(l.id) &&
                        l.uredjaji.map((u) => (
                          <button
                            key={u.id}
                            type="button"
                            onClick={() => onOdabir({ tip: 'uredjaj', id: u.id })}
                            className={cn(
                              'ml-5 flex w-[calc(100%-1.25rem)] items-center gap-2 rounded px-2 py-1 text-left text-[11px] hover:bg-slate-50',
                              isOdabran('uredjaj', u.id) &&
                                'bg-[#0054A6] text-white hover:bg-[#0054A6]',
                            )}
                          >
                            <span className="font-mono text-[10px] opacity-75">
                              {u.uredjaj_tip}
                            </span>
                            <span className="truncate">{u.naziv}</span>
                            <Badge count={u.ukupno} />
                          </button>
                        ))}
                    </div>
                  ))}
              </div>
            ))}
        </div>
      ))}
    </div>
  )
}
