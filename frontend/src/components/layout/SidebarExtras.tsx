import { ChevronRight, MapPin, Server } from 'lucide-react'
import { useState } from 'react'
import { LokacijeSheet } from '@/components/layout/LokacijeSheet'
import { MsanSheet } from '@/components/layout/MsanSheet'

interface SidebarExtrasProps {
  /** Zatvori sidebar (mobile) kad se otvori panel ili klikne lokacija. */
  onNavigate: () => void
}

/**
 * Sidebar dodaci: dvije stavke koje otvaraju desni slide-over panel
 * (Sheet). Nema više accordion dropdown-a.
 *
 * TODO(Vitest): kad Vitest bude dodan u package.json, dodati
 * `Sidebar.test.tsx` koji testira da klik na "Lokacije" otvara Sheet.
 */
export function SidebarExtras({ onNavigate }: SidebarExtrasProps) {
  const [lokacijeOpen, setLokacijeOpen] = useState(false)
  const [msanOpen, setMsanOpen] = useState(false)

  const otvoriLokacije = () => {
    onNavigate()
    setLokacijeOpen(true)
  }
  const otvoriMsan = () => {
    onNavigate()
    setMsanOpen(true)
  }

  return (
    <>
      <span className="mt-3 block space-y-1 border-t border-slate-100 pt-3">
        <button
          type="button"
          onClick={otvoriLokacije}
          aria-label="Otvori panel s lokacijama"
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 transition-all hover:bg-[#0054A6]/8 hover:text-[#0054A6]"
        >
          <MapPin className="h-5 w-5 shrink-0" />
          <span className="flex-1 text-left">Lokacije</span>
          <ChevronRight className="h-4 w-4 text-slate-400" />
        </button>
        <button
          type="button"
          onClick={otvoriMsan}
          aria-label="Otvori panel s MSAN uređajima"
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 transition-all hover:bg-[#0054A6]/8 hover:text-[#0054A6]"
        >
          <Server className="h-5 w-5 shrink-0" />
          <span className="flex-1 text-left">MSAN uređaji</span>
          <ChevronRight className="h-4 w-4 text-slate-400" />
        </button>
      </span>

      <LokacijeSheet open={lokacijeOpen} onOpenChange={setLokacijeOpen} />
      <MsanSheet open={msanOpen} onOpenChange={setMsanOpen} />
    </>
  )
}
