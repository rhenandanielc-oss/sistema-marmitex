import type { ReactNode } from 'react'

import { cx } from './ui'

export function Kpi({ label, value, hint, tone = 'default', emphasis }: {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: 'default' | 'positive' | 'negative'
  emphasis?: boolean
}) {
  return (
    <div className={cx('rounded-lg border bg-white p-4 shadow-sm',
      emphasis ? 'border-brand-500/40 ring-1 ring-brand-500/20' : 'border-slate-200')}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={cx('tabular mt-1 font-semibold', emphasis ? 'text-2xl' : 'text-xl',
        tone === 'positive' && 'text-emerald-700', tone === 'negative' && 'text-red-700',
        tone === 'default' && 'text-slate-900')}>
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}
