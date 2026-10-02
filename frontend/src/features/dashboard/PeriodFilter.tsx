import { useSearchParams } from 'react-router-dom'

import type { PeriodPreset } from '../../api/types'
import { Button, Input, cx } from '../../components/ui'
import { todayIso } from '../../lib/format'

const PRESETS: { value: PeriodPreset; label: string }[] = [
  { value: 'today', label: 'Hoje' },
  { value: 'week', label: 'Semana' },
  { value: 'month', label: 'Mês' },
  { value: 'last_month', label: 'Mês anterior' },
  { value: 'custom', label: 'Personalizado' },
]

/** Lê o período da URL (?periodo=&inicio=&fim=) e devolve os parâmetros da API. */
export function usePeriodParams(): { preset: PeriodPreset; params: Record<string, string> } {
  const [search] = useSearchParams()
  const preset = (search.get('periodo') as PeriodPreset | null) ?? 'month'
  const params: Record<string, string> = { period: preset }
  if (preset === 'custom') {
    params.start_date = search.get('inicio') ?? `${todayIso().slice(0, 8)}01`
    params.end_date = search.get('fim') ?? todayIso()
  }
  return { preset, params }
}

export function PeriodFilter() {
  const [search, setSearch] = useSearchParams()
  const { preset, params } = usePeriodParams()

  const update = (changes: Record<string, string | null>) => {
    const next = new URLSearchParams(search)
    for (const [k, v] of Object.entries(changes)) {
      if (v === null) next.delete(k)
      else next.set(k, v)
    }
    setSearch(next, { replace: true })
  }

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Período">
      {PRESETS.map((p) => (
        <Button key={p.value} variant={preset === p.value ? 'primary' : 'secondary'} aria-pressed={preset === p.value}
          onClick={() => update(p.value === 'custom'
            ? { periodo: 'custom', inicio: params.start_date ?? `${todayIso().slice(0, 8)}01`, fim: params.end_date ?? todayIso() }
            : { periodo: p.value, inicio: null, fim: null })}>
          {p.label}
        </Button>
      ))}
      {preset === 'custom' && (
        <div className={cx('flex items-center gap-2')}>
          <Input type="date" aria-label="Data inicial" value={params.start_date} onChange={(e) => update({ inicio: e.target.value })} />
          <span className="text-sm text-slate-500">até</span>
          <Input type="date" aria-label="Data final" value={params.end_date} onChange={(e) => update({ fim: e.target.value })} />
        </div>
      )}
    </div>
  )
}
