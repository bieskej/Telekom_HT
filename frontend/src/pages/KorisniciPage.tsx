import { useCallback, useEffect, useMemo, useState } from 'react'
import { Search, Users } from 'lucide-react'
import { toast } from 'sonner'
import { api, mapApiError } from '@/lib/api'
import { FILTER_ALL } from '@/lib/constants'
import type { KorisnikItem } from '@/types/api'
import { KorisnikKartica } from '@/components/korisnici/KorisnikKartica'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { CardGridSkeleton } from '@/components/ui/TableSkeleton'

type FilterKorisnika = typeof FILTER_ALL | 'ima_zauzet' | 'ima_karantena' | 'samo_karantena'

export function KorisniciPage() {
  const [korisnici, setKorisnici] = useState<KorisnikItem[]>([])
  const [loading, setLoading] = useState(true)
  const [pretraga, setPretraga] = useState('')
  const [filterKorisnika, setFilterKorisnika] = useState<FilterKorisnika>(FILTER_ALL)

  const ucitajKorisnike = useCallback(() => {
    setLoading(true)
    api
      .korisnici()
      .then(setKorisnici)
      .catch((e) => {
        const msg = mapApiError(e, 'Korisnici nisu učitani.')
        if (msg.toLowerCase().includes('not found')) {
          toast.error(
            'API /korisnici nije dostupan. Restartajte backend: .\\scripts\\start-backend.ps1 (port 8004).',
          )
        } else {
          toast.error(msg)
        }
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    ucitajKorisnike()
  }, [ucitajKorisnike])

  const filtrirani = useMemo(() => {
    let lista = korisnici

    if (filterKorisnika === 'ima_zauzet') {
      lista = lista.filter((k) => k.broj_zauzet > 0)
    } else if (filterKorisnika === 'ima_karantena') {
      lista = lista.filter((k) => k.broj_karantena > 0)
    } else if (filterKorisnika === 'samo_karantena') {
      lista = lista.filter((k) => k.broj_karantena > 0 && k.broj_zauzet === 0)
    }

    const q = pretraga.trim().toLowerCase()
    if (!q) return lista
    return lista.filter(
      (k) =>
        k.ime.toLowerCase().includes(q) ||
        k.prezime.toLowerCase().includes(q) ||
        k.jmbg.includes(q) ||
        (k.email ?? '').toLowerCase().includes(q),
    )
  }, [korisnici, pretraga, filterKorisnika])

  const prazanFilter =
    !loading &&
    korisnici.length > 0 &&
    filtrirani.length === 0 &&
    (pretraga.trim() !== '' || filterKorisnika !== FILTER_ALL)

  const nemaKorisnika = !loading && korisnici.length === 0

  return (
    <span className="block space-y-6">
      <Card className="grid gap-4 p-4 sm:grid-cols-2 lg:p-6">
        <Input
          label="Pretraga korisnika"
          value={pretraga}
          onChange={(e) => setPretraga(e.target.value)}
          placeholder="Ime, prezime, JMBG ili email"
        />
        <Select
          label="Filter korisnika"
          value={filterKorisnika}
          onValueChange={(v) => setFilterKorisnika(v as FilterKorisnika)}
          options={[
            { value: FILTER_ALL, label: 'Svi korisnici' },
            { value: 'ima_zauzet', label: 'Ima aktivnih (zauzet)' },
            { value: 'ima_karantena', label: 'Ima u karanteni' },
            { value: 'samo_karantena', label: 'Samo karantena' },
          ]}
        />
      </Card>

      {loading ? (
        <CardGridSkeleton />
      ) : nemaKorisnika ? (
        <EmptyState
          icon={Users}
          title="Nema korisnika u sustavu"
          description="Korisnici se pojavljuju nakon dodjele brojeva (zauzet status)."
          action={{ label: 'Idi na dodjelu', to: '/dodjela' }}
        />
      ) : prazanFilter ? (
        <EmptyState
          icon={Search}
          title="Nema korisnika za filter"
          description="Pokušajte drugu pretragu ili uklonite filter korisnika."
        />
      ) : (
        <span className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtrirani.map((k) => (
            <KorisnikKartica key={k.jmbg} korisnik={k} onRefresh={ucitajKorisnike} />
          ))}
        </span>
      )}
    </span>
  )
}
