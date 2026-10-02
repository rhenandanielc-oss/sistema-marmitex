/**
 * Formatação para exibição (pt-BR). Nenhum cálculo financeiro é feito aqui:
 * os valores chegam prontos da API como strings decimais ("1234.50").
 */

const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const integer = new Intl.NumberFormat('pt-BR')
const decimal2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const EMPTY = '—'

export function formatMoney(value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return EMPTY
  return currency.format(Number(value))
}

export function formatInt(value: number | null | undefined): string {
  if (value === null || value === undefined) return EMPTY
  return integer.format(value)
}

export function formatPercent(value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return EMPTY
  return `${decimal2.format(Number(value))}%`
}

/** "2026-09-01" → "01/09/2026" */
export function formatDate(value: string | null | undefined): string {
  if (!value) return EMPTY
  const [y, m, d] = value.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

/** "2026-09-01" → "01/09" (rótulos de gráfico) */
export function formatDayMonth(value: string): string {
  const [, m, d] = value.split('-')
  return `${d}/${m}`
}

/** Data local de hoje como "AAAA-MM-DD" (valor inicial de campos; o servidor valida). */
export function todayIso(now: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function isNegative(value: string | null | undefined): boolean {
  return !!value && value.trim().startsWith('-')
}

export const BILLING_CYCLE_LABELS: Record<string, string> = {
  A_VISTA: 'À vista',
  SEMANAL: 'Semanal',
  QUINZENAL: 'Quinzenal',
  MENSAL: 'Mensal',
}

export const COST_TYPE_LABELS: Record<string, string> = {
  CUSTO_DIARIO: 'Diário',
  CUSTO_FIXO: 'Fixo',
}

export const BUYER_TYPE_LABELS: Record<string, string> = {
  COMPANY: 'Empresa',
  CUSTOMER: 'Cliente avulso',
}

export function formatCnpj(value: string | null | undefined): string {
  if (!value) return EMPTY
  if (value.length !== 14) return value
  return `${value.slice(0, 2)}.${value.slice(2, 5)}.${value.slice(5, 8)}/${value.slice(8, 12)}-${value.slice(12)}`
}
