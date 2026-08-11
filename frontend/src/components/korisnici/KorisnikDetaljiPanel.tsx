import { Link } from 'react-router-dom'
import { Mail, Phone, UserCircle, X } from 'lucide-react'
import type { KorisnikItem, MsisdnItem } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface KorisnikDetaljiPanelProps {
  korisnik: KorisnikItem
  brojevi?: MsisdnItem[]
  loadingBrojevi?: boolean
  maxBrojeva?: number
  onZatvori?: () => void
  /** Kad smo već na /brojevi s filterom JMBG-a, link je suvišan. */
  sakrijLinkBrojeva?: boolean
}

export function KorisnikDetaljiPanel({
  korisnik,
  brojevi = [],
  loadingBrojevi = false,
  maxBrojeva = 5,
  onZatvori,
  sakrijLinkBrojeva = false,
}: KorisnikDetaljiPanelProps) {
  const prikaz = brojevi.slice(0, maxBrojeva)
  const linkBrojevi = `/brojevi?korisnik_jmbg=${encodeURIComponent(korisnik.jmbg)}`

  return (
    <Card className="border-[#0054A6]/25 bg-gradient-to-br from-[#e6f7fc]/80 to-white p-4 lg:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <span className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#0054A6]/10 text-[#0054A6]">
            <UserCircle className="h-7 w-7" />
          </span>
          <span>
            <p className="text-lg font-semibold text-slate-900">
              {korisnik.ime} {korisnik.prezime}
            </p>
            <p className="mt-0.5 font-mono text-sm text-slate-600">JMBG: {korisnik.jmbg}</p>
          </span>
        </span>
        {onZatvori && (
          <Button type="button" variant="ghost" size="sm" onClick={onZatvori} aria-label="Zatvori">
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Email</dt>
          <dd className="flex items-center gap-1.5 font-medium text-slate-800">
            <Mail className="h-3.5 w-3.5 shrink-0 text-slate-400" />
            {korisnik.email ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Dodijeljenih brojeva</dt>
          <dd className="font-semibold text-[#0054A6]">{korisnik.broj_brojeva}</dd>
        </div>
      </dl>

      {(loadingBrojevi || prikaz.length > 0) && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Zadnji brojevi
          </p>
          {loadingBrojevi ? (
            <p className="text-sm text-slate-500">Učitavanje brojeva…</p>
          ) : (
            <ul className="space-y-1.5">
              {prikaz.map((b) => (
                <li
                  key={b.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm"
                >
                  <span className="flex items-center gap-2 font-medium text-slate-800">
                    <Phone className="h-3.5 w-3.5 text-[#00A3E0]" />
                    {b.broj_formatiran}
                  </span>
                  <Badge variant={b.status as 'slobodan' | 'zauzet' | 'karantena'}>{b.status}</Badge>
                </li>
              ))}
            </ul>
          )}
          {!loadingBrojevi && korisnik.broj_brojeva > maxBrojeva && (
            <p className="mt-2 text-xs text-slate-500">
              Prikazano {prikaz.length} od {korisnik.broj_brojeva} brojeva.
            </p>
          )}
        </div>
      )}

      {!sakrijLinkBrojeva && (
        <div className="mt-4">
          <Link to={linkBrojevi}>
            <Button variant="outline" size="sm" type="button">
              Svi brojevi korisnika
            </Button>
          </Link>
        </div>
      )}
    </Card>
  )
}
