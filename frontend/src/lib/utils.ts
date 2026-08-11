import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { msisdnStatusLabel } from '@/lib/statusUi'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** @deprecated Preferiraj msisdnStatusLabel iz statusUi */
export function formatStatus(status: string): string {
  return msisdnStatusLabel(status)
}

export function exportToCsv(rows: Record<string, string | number | null | undefined>[], filename: string) {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv = [
    headers.join(';'),
    ...rows.map((r) => headers.map((h) => `"${String(r[h] ?? '').replace(/"/g, '""')}"`).join(';')),
  ].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
