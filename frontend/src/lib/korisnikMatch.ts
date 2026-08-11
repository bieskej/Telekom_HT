import type { KorisnikItem } from '@/types/api'

export function normalizeKorisnikPretraga(q: string): string {
  return q.trim().toLowerCase().replace(/\s+/g, ' ')
}

export function korisnikOdgovaraUpitu(k: KorisnikItem, upit: string): boolean {
  const n = normalizeKorisnikPretraga(upit)
  if (!n) return false
  const puno = `${k.ime} ${k.prezime}`.toLowerCase()
  const obrnuto = `${k.prezime} ${k.ime}`.toLowerCase()
  return (
    puno.includes(n) ||
    obrnuto.includes(n) ||
    k.jmbg.includes(upit.trim()) ||
    (k.email ?? '').toLowerCase().includes(n)
  )
}

export function pronadjiKorisnikaPoJmbg(
  korisnici: KorisnikItem[],
  jmbg: string,
): KorisnikItem | null {
  const j = jmbg.trim()
  if (!j) return null
  return korisnici.find((k) => k.jmbg === j) ?? null
}

/** Vrati korisnika samo ako upit jednoznačno odgovara točno jednom. */
export function pronadjiJedinstvenogKorisnika(
  korisnici: KorisnikItem[],
  upit: string,
): KorisnikItem | null {
  const q = upit.trim()
  if (!q) return null
  const poklopci = korisnici.filter((k) => korisnikOdgovaraUpitu(k, q))
  return poklopci.length === 1 ? poklopci[0] : null
}
