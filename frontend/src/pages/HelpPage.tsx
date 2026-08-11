import { Link } from 'react-router-dom'
import {
  BarChart3,
  CircleHelp,
  Hash,
  PhoneCall,
  ShieldAlert,
  UserCircle,
  Users,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

interface HelpSection {
  id: string
  title: string
  icon: typeof CircleHelp
  body: string
  links: { label: string; to: string }[]
}

const SECTIONS: HelpSection[] = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    icon: BarChart3,
    body: 'Pregled iskorištenosti inventara: KPI kartice, heatmap dodjela, grafikon i interaktivna mapa općina. Klik na općinu na mapi otvara listu brojeva s filterom općine. Boje zauzetosti: zeleno (<50%), narančasto (50–90%), crveno (≥90%). Ispis: gumb „Ispiši” na dashboardu — sidebar i navigacija se skrivaju; interaktivna mapa se ne ispisuje (samo KPI, heatmap i grafikoni).',
    links: [{ label: 'Otvori dashboard', to: '/' }],
  },
  {
    id: 'dodjela',
    title: 'Dodjela',
    icon: PhoneCall,
    body: 'Prodaja dodjeljuje slobodan broj kupcu: odabir općine i kvalitete, rezervacija 5 minuta, unos JMBG-a i podataka za ugovor. Nakon potvrde generiraju se PDF ugovor i račun; email se šalje ako je konfiguriran.',
    links: [
      { label: 'Nova dodjela', to: '/dodjela' },
      { label: 'Bulk dodjela', to: '/dodjela?bulk=1' },
    ],
  },
  {
    id: 'karantena',
    title: 'Karantena',
    icon: ShieldAlert,
    body: 'Zauzeti brojevi mogu ući u karantenu (zadani rok 60 dana, prodaja može odabrati trajanje). Admin može skratiti rok ili odmah osloboditi broj. Pregled korisnika s brojevima u karanteni: filter na stranici Korisnici ili status „Karantena” na Brojevi.',
    links: [
      { label: 'Korisnici', to: '/korisnici' },
      { label: 'Brojevi — karantena', to: '/brojevi?status=karantena' },
    ],
  },
  {
    id: 'brojevi',
    title: 'Brojevi',
    icon: Hash,
    body: 'Pretraga inventara po broju, korisniku, statusu, općini i kvaliteti. Magični broj (*uzorak) za brzi odabir slobodnog broja za dodjelu. Filteri se mogu dijeliti putem URL-a (status, općina, stranica).',
    links: [{ label: 'Pretraga brojeva', to: '/brojevi' }],
  },
  {
    id: 'portal',
    title: 'Portal kupca',
    icon: UserCircle,
    body: 'Kupac se registrira s JMBG-om koji odgovara dodijeljenim brojevima (inline provjera emaila, lozinke i JMBG-a). Nakon prijave vidi svoje brojeve i može preuzeti ugovor. Vizual portala usklađen je sa staff aplikacijom (Card, Button, Input). Staff i portal imaju odvojene prijave.',
    links: [
      { label: 'Portal — prijava', to: '/portal/prijava' },
      { label: 'Portal — registracija', to: '/portal/registracija' },
    ],
  },
  {
    id: 'uloge',
    title: 'Uloge',
    icon: Users,
    body: 'admin — puni pristup (import RAK, audit, servisni nalozi, oslobađanje iz karantene). prodaja — dodjela, portabilnost, karantena. promet — pregled statistike i brojeva. kupac — samo portal (/portal/*), ne koristi staff prijavu.',
    links: [
      { label: 'Radnici (admin)', to: '/radnici' },
      { label: 'Staff prijava', to: '/prijava' },
    ],
  },
]

export function HelpPage() {
  return (
    <span className="block space-y-6">
      <Card className="border-[#0054A6]/15 bg-gradient-to-br from-[#e6f7fc]/40 to-white dark:from-slate-900 dark:to-slate-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#0054A6]">
            <CircleHelp className="h-6 w-6" />
            Pomoć — HT Eronet
          </CardTitle>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Kratki vodič kroz glavne module. Detaljniji tokovi:{' '}
            <code className="rounded bg-slate-100 px-1 text-xs dark:bg-slate-800">docs/USER_FLOWS.md</code>
          </p>
        </CardHeader>
      </Card>

      <span className="grid gap-4 lg:grid-cols-2">
        {SECTIONS.map((s) => (
          <Card key={s.id} id={s.id} className="scroll-mt-24">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <s.icon className="h-5 w-5 text-[#0054A6]" aria-hidden />
                {s.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <p>{s.body}</p>
              <span className="flex flex-wrap gap-2">
                {s.links.map((l) => (
                  <Link
                    key={l.to}
                    to={l.to}
                    className="inline-flex rounded-lg border border-[#0054A6]/20 bg-[#0054A6]/5 px-3 py-1.5 text-sm font-medium text-[#0054A6] hover:bg-[#0054A6]/10 dark:border-[#00A3E0]/30 dark:text-[#00A3E0]"
                  >
                    {l.label}
                  </Link>
                ))}
              </span>
            </CardContent>
          </Card>
        ))}
      </span>
    </span>
  )
}
