/**
 * Gráficos (Recharts). Apenas desenho: todos os valores vêm prontos da API.
 * Paleta categórica validada (dataviz/validate_palette.js, modo claro): ordem fixa, nunca reciclada.
 * Três cores ficam abaixo de 3:1 de contraste → todo gráfico tem "Ver tabela" (alívio exigido).
 */
import { useState, type ReactNode } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip,
  XAxis, YAxis } from 'recharts'

import { formatDate, formatDayMonth, formatInt, formatMoney } from '../lib/format'
import { Button, Card, Table, Td, Th } from './ui'

export const SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
export const COLORS = {
  revenue: SERIES[0],
  costs: SERIES[1],
  profit: SERIES[2],
  dailyCosts: SERIES[1],
  fixedCosts: SERIES[6],
  quantity: SERIES[0],
  negative: '#e34948', // polo negativo (vermelho) do par divergente azul↔vermelho
  positive: '#2a78d6',
  grid: '#e7e5e4',
  axis: '#78716c',
}

const AXIS_TICK = { fontSize: 11, fill: COLORS.axis }

export type Row = Record<string, string | number | null>
export interface SeriesSpec {
  key: string
  label: string
  color: string
  kind?: 'money' | 'int'
}

function fmt(value: unknown, kind: 'money' | 'int' = 'money'): string {
  if (value === null || value === undefined) return '—'
  return kind === 'int' ? formatInt(Number(value)) : formatMoney(String(value))
}

const NBSP = '\u00a0' // espaço que não quebra (evita rótulo do eixo em duas linhas)

export function compactMoney(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1000) {
    return `${value < 0 ? '-' : ''}R$${NBSP}${(abs / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}${NBSP}mil`
  }
  return `R$${NBSP}${value.toLocaleString('pt-BR')}`
}

/** Converte strings decimais da API em números somente para posicionar as marcas no gráfico. */
function toPlot(rows: Row[], series: SeriesSpec[]): Row[] {
  return rows.map((r) => {
    const out: Row = { ...r }
    for (const s of series) out[`__${s.key}`] = r[s.key] === null ? null : Number(r[s.key])
    return out
  })
}

function ChartTooltip({ active, payload, label, series }: {
  active?: boolean
  payload?: { dataKey?: string | number; payload: Row }[]
  label?: string
  series: SeriesSpec[]
}) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md">
      <div className="mb-1 font-semibold text-slate-800">{label && /^\d{4}-\d{2}-\d{2}$/.test(label) ? formatDate(label) : label}</div>
      {series.map((s) => (
        <div key={s.key} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />{s.label}
          </span>
          <span className="tabular font-medium text-slate-900">{fmt(row[s.key], s.kind)}</span>
        </div>
      ))}
    </div>
  )
}

/** Cartão de gráfico com alternância para tabela (acessibilidade / contraste). */
export function ChartCard({ title, subtitle, rows, series, xKey, xLabel, empty, children }: {
  title: string
  subtitle?: ReactNode
  rows: Row[]
  series: SeriesSpec[]
  xKey: string
  xLabel: string
  empty?: boolean
  children: ReactNode
}) {
  const [asTable, setAsTable] = useState(false)
  return (
    <Card title={<span>{title}{subtitle && <span className="ml-2 text-xs font-normal text-slate-500">{subtitle}</span>}</span>}
      actions={<Button variant="ghost" onClick={() => setAsTable(!asTable)}>{asTable ? 'Ver gráfico' : 'Ver tabela'}</Button>}>
      {empty ? (
        <div className="flex h-64 items-center justify-center text-sm text-slate-500">Nenhum lançamento no período.</div>
      ) : asTable ? (
        <div className="max-h-72 overflow-y-auto">
          <Table>
            <thead><tr><Th>{xLabel}</Th>{series.map((s) => <Th key={s.key} className="text-right">{s.label}</Th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr key={String(r[xKey])}>
                  <Td className="tabular">{/^\d{4}-\d{2}-\d{2}$/.test(String(r[xKey])) ? formatDate(String(r[xKey])) : r[xKey]}</Td>
                  {series.map((s) => <Td key={s.key} className="tabular text-right">{fmt(r[s.key], s.kind)}</Td>)}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : (
        <div className="h-64">{children}</div>
      )}
    </Card>
  )
}

function xTick(value: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? formatDayMonth(value) : value
}

/** Barras verticais por dia. `signed` colore negativos com o polo vermelho. */
export function DailyBars({ rows, series, signed, stacked }: {
  rows: Row[]
  series: SeriesSpec[]
  signed?: boolean
  stacked?: boolean
}) {
  const data = toPlot(rows, series)
  const kind = series[0]?.kind ?? 'money'
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }} barCategoryGap={2}>
        <CartesianGrid vertical={false} stroke={COLORS.grid} />
        <XAxis dataKey="date" tickFormatter={xTick} tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: COLORS.grid }}
          minTickGap={12} />
        <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} width={88}
          tickFormatter={(v: number) => (kind === 'int' ? formatInt(v) : compactMoney(v))} />
        <Tooltip cursor={{ fill: 'rgba(15,23,42,0.05)' }} content={<ChartTooltip series={series} />} />
        {series.length > 1 && <Legend iconType="circle" itemSorter={null} wrapperStyle={{ fontSize: 12 }} />}
        {signed && <ReferenceLine y={0} stroke={COLORS.axis} />}
        {series.map((s, i) => (
          <Bar key={s.key} dataKey={`__${s.key}`} name={s.label} fill={s.color} stackId={stacked ? 'stack' : undefined}
            radius={signed ? 0 : stacked && i < series.length - 1 ? 0 : [4, 4, 0, 0]} maxBarSize={28}
            stroke={stacked ? '#ffffff' : undefined} strokeWidth={stacked ? 1 : 0}>
            {signed && data.map((d) => (
              <Cell key={String(d.date)} fill={Number(d[`__${s.key}`]) < 0 ? COLORS.negative : COLORS.positive} />
            ))}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Linhas por dia (mesma unidade — um único eixo). */
export function DailyLines({ rows, series }: { rows: Row[]; series: SeriesSpec[] }) {
  const data = toPlot(rows, series)
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid vertical={false} stroke={COLORS.grid} />
        <XAxis dataKey="date" tickFormatter={xTick} tick={AXIS_TICK} tickLine={false} axisLine={{ stroke: COLORS.grid }}
          minTickGap={12} />
        <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} width={88} tickFormatter={compactMoney} />
        <Tooltip content={<ChartTooltip series={series} />} />
        <Legend iconType="circle" itemSorter={null} wrapperStyle={{ fontSize: 12 }} />
        <ReferenceLine y={0} stroke={COLORS.grid} />
        {series.map((s) => (
          <Line key={s.key} type="linear" dataKey={`__${s.key}`} name={s.label} stroke={s.color} strokeWidth={2}
            dot={false} activeDot={{ r: 4, stroke: '#ffffff', strokeWidth: 2 }} isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

/** Barras horizontais (ranking). Uma série → uma cor. */
export function RankingBars({ rows, valueKey, labelKey, label }: {
  rows: Row[]
  valueKey: string
  labelKey: string
  label: string
}) {
  const series: SeriesSpec[] = [{ key: valueKey, label, color: COLORS.revenue }]
  const data = toPlot(rows, series)
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }} barCategoryGap={4}>
        <CartesianGrid horizontal={false} stroke={COLORS.grid} />
        <XAxis type="number" tick={AXIS_TICK} tickLine={false} axisLine={false} tickFormatter={compactMoney} />
        <YAxis type="category" dataKey={labelKey} tick={AXIS_TICK} tickLine={false} axisLine={false} width={150} />
        <Tooltip cursor={{ fill: 'rgba(15,23,42,0.05)' }} content={<ChartTooltip series={series} />} />
        <Bar dataKey={`__${valueKey}`} name={label} fill={COLORS.revenue} radius={[0, 4, 4, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  )
}
