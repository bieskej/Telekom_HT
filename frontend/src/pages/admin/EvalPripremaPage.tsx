import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ClipboardCopy, Download, ExternalLink, FlaskConical } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import {
  EVAL_CHECKLIST_MARKDOWN,
  EVAL_SCENARIOS,
  EVAL_TEST_ACCOUNTS,
  SUS_FORM_URL,
} from '@/data/evalPriprema'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

const IS_DEV = import.meta.env.DEV

export function EvalPripremaPage() {
  const { hasUloga } = useAuth()
  const [copied, setCopied] = useState(false)

  if (!hasUloga('admin')) {
    return <Navigate to="/" replace />
  }

  if (!IS_DEV) {
    return (
      <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30">
        <CardContent className="py-8 text-center text-sm text-amber-900 dark:text-amber-200">
          Stranica Eval priprema dostupna je samo u development buildu (`npm run dev`).
        </CardContent>
      </Card>
    )
  }

  const kopirajPodatke = async () => {
    try {
      await navigator.clipboard.writeText(EVAL_TEST_ACCOUNTS)
      setCopied(true)
      toast.success('Testni podaci kopirani u međuspremnik')
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Kopiranje nije uspjelo')
    }
  }

  const preuzmiChecklist = () => {
    const blob = new Blob([EVAL_CHECKLIST_MARKDOWN], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'eronet-eval-checklist-testera.md'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Checklist preuzet')
  }

  return (
    <span className="block space-y-6">
      <Card className="border-violet-200 bg-violet-50/80 dark:border-violet-900 dark:bg-violet-950/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-violet-900 dark:text-violet-200">
            <FlaskConical className="h-5 w-5" />
            Eval priprema (dev-only)
          </CardTitle>
          <p className="text-sm text-violet-800 dark:text-violet-300">
            Protokol iz{' '}
            <code className="rounded bg-white/60 px-1 dark:bg-slate-900">docs/EVALUACIJA_KS.md</code>.
            Nema novih API endpointa.
          </p>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button type="button" variant="primary" onClick={() => void kopirajPodatke()}>
            <ClipboardCopy className="h-4 w-4" />
            {copied ? 'Kopirano!' : 'Kopiraj testne podatke'}
          </Button>
          <Button type="button" variant="outline" onClick={preuzmiChecklist}>
            <Download className="h-4 w-4" />
            Preuzmi checklist (Markdown)
          </Button>
          {SUS_FORM_URL ? (
            <a
              href={SUS_FORM_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-[10px] border-2 border-[#0054A6]/20 px-4 py-2 text-sm font-medium text-[#0054A6] hover:bg-[#e6f2fa] dark:border-slate-600 dark:text-[#00A3E0] dark:hover:bg-slate-800"
            >
              <ExternalLink className="h-4 w-4" />
              SUS Google Form
            </a>
          ) : (
            <span className="text-xs text-slate-600 dark:text-slate-400 self-center">
              SUS forma: postavi <code>VITE_SUS_FORM_URL</code> u .env.local ili koristi Markdown checklist.
            </span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scenariji zadataka (T1–T8)</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-600 dark:bg-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Zadatak</th>
                <th className="px-3 py-2">Uloga</th>
                <th className="px-3 py-2">Početak</th>
                <th className="px-3 py-2">Kriterij</th>
              </tr>
            </thead>
            <tbody>
              {EVAL_SCENARIOS.map((s) => (
                <tr key={s.id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-mono font-semibold">{s.id}</td>
                  <td className="px-3 py-2">{s.task}</td>
                  <td className="px-3 py-2 text-slate-600 dark:text-slate-400">{s.persona}</td>
                  <td className="px-3 py-2">
                    <Link
                      to={s.startUrl}
                      className="font-medium text-[#0054A6] hover:underline dark:text-[#00A3E0]"
                    >
                      {s.startUrl}
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-slate-600 dark:text-slate-400">{s.success}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-600 dark:text-slate-400">
            T4 + T8: koristite demo JMBG <code>0101000500012</code> ili isti JMBG pri registraciji i dodjeli.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Testni računi (pregled)</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-800 dark:bg-slate-950 dark:text-slate-200">
            {EVAL_TEST_ACCOUNTS}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Povezano</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 text-sm">
          <Link to="/pomoc" className="text-[#0054A6] hover:underline dark:text-[#00A3E0]">
            Pomoć u aplikaciji
          </Link>
          <span className="text-slate-400">·</span>
          <a
            href="https://github.com"
            className="text-slate-600 dark:text-slate-400"
            onClick={(e) => {
              e.preventDefault()
              toast.info('Puni protokol: docs/EVALUACIJA_KS.md u repozitoriju')
            }}
          >
            EVALUACIJA_KS.md (repo)
          </a>
        </CardContent>
      </Card>
    </span>
  )
}
