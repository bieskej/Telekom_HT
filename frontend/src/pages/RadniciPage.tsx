import { Navigate } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { Radnik } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Badge } from '@/components/ui/Badge'

export function RadniciPage() {
  const { hasUloga } = useAuth()
  const [radnici, setRadnici] = useState<Radnik[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [email, setEmail] = useState('')
  const [ime, setIme] = useState('')
  const [prezime, setPrezime] = useState('')
  const [lozinka, setLozinka] = useState('')
  const [jmbg, setJmbg] = useState('')
  const [uloga, setUloga] = useState('prodaja')
  const [loading, setLoading] = useState(false)

  const ucitaj = useCallback(() => {
    setLoadingList(true)
    api
      .listaRadnika()
      .then(setRadnici)
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Greška'))
      .finally(() => setLoadingList(false))
  }, [])

  useEffect(() => {
    if (hasUloga('admin')) ucitaj()
  }, [hasUloga, ucitaj])

  if (!hasUloga('admin')) {
    return <Navigate to="/" replace />
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.kreirajRadnika({
        email,
        ime,
        prezime,
        lozinka,
        uloga,
        jmbg: uloga === 'kupac' && jmbg ? jmbg : undefined,
      })
      toast.success('Korisnik je kreiran')
      setEmail('')
      setIme('')
      setPrezime('')
      setLozinka('')
      setJmbg('')
      ucitaj()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Greška')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Novi korisnik</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Ime" value={ime} onChange={(e) => setIme(e.target.value)} required />
            <Input label="Prezime" value={prezime} onChange={(e) => setPrezime(e.target.value)} required />
            <Input label="Lozinka" type="password" value={lozinka} onChange={(e) => setLozinka(e.target.value)} required />
            <Select
              label="Uloga"
              value={uloga}
              onValueChange={setUloga}
              options={[
                { value: 'admin', label: 'Admin' },
                { value: 'prodaja', label: 'Prodaja' },
                { value: 'promet', label: 'Promet' },
                { value: 'kupac', label: 'Kupac (portal)' },
              ]}
            />
            {uloga === 'kupac' && (
              <Input
                label="JMBG (obavezno za kupca)"
                value={jmbg}
                onChange={(e) => setJmbg(e.target.value.replace(/\D/g, '').slice(0, 13))}
                maxLength={13}
                required
              />
            )}
            <Button type="submit" loading={loading}>
              Kreiraj
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Svi korisnici ({radnici.length})</CardTitle>
          <p className="text-sm text-slate-500">Uključujući kupce registrirane putem portala</p>
        </CardHeader>
        <CardContent>
          {loadingList && <p className="text-sm text-slate-400">Učitavanje…</p>}
          {!loadingList && (
            <div className="overflow-x-auto rounded-lg border border-slate-100">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Ime</th>
                    <th className="px-3 py-2">Email</th>
                    <th className="px-3 py-2">Uloga</th>
                    <th className="px-3 py-2">JMBG</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {radnici.map((r) => (
                    <tr key={r.id} className="border-t border-slate-50">
                      <td className="px-3 py-2">
                        {r.ime} {r.prezime}
                      </td>
                      <td className="px-3 py-2">{r.email}</td>
                      <td className="px-3 py-2">
                        <Badge variant={r.uloga === 'kupac' ? 'default' : 'zauzet'}>
                          {r.uloga}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">{r.jmbg ?? '—'}</td>
                      <td className="px-3 py-2">{r.aktivan ? 'Aktivan' : 'Neaktivan'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
