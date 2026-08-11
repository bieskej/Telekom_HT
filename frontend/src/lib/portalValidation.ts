export function validirajJmbg(jmbg: string): boolean {
  if (!/^\d{13}$/.test(jmbg)) return false
  const w = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
  let s = 0
  for (let i = 0; i < 12; i++) s += parseInt(jmbg[i], 10) * w[i]
  let k = 11 - (s % 11)
  if (k === 10 || k === 11) k = 0
  return k === parseInt(jmbg[12], 10)
}

export function validirajEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

export function inlineEmailError(email: string): string | undefined {
  if (!email.trim()) return undefined
  if (!validirajEmail(email)) return 'Unesite ispravnu email adresu.'
  return undefined
}

export function inlineJmbgError(jmbg: string): string | undefined {
  if (jmbg.length === 0) return undefined
  if (jmbg.length < 13) return 'JMBG mora imati 13 znamenki.'
  if (!validirajJmbg(jmbg)) return 'Neispravan JMBG (modul 11).'
  return undefined
}

export function inlineLozinkaError(lozinka: string, min = 4): string | undefined {
  if (lozinka.length === 0) return undefined
  if (lozinka.length < min) return `Lozinka mora imati najmanje ${min} znaka.`
  return undefined
}
