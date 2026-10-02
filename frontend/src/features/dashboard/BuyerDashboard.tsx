import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { api, errorMessage } from '../../api/client'
import type { BuyerDashboard as BuyerDashboardData, BuyerType } from '../../api/types'
import { ChartCard, COLORS, DailyBars, type Row } from '../../components/charts'
import { DeliveryBadge, PaymentBadge } from '../../components/badges'
import { Kpi } from '../../components/Kpi'
import { ActiveBadge, Button, Card, ErrorBox, Loading, PageHeader, Table, Td, Th } from '../../components/ui'
import { BILLING_CYCLE_LABELS, BUYER_TYPE_LABELS, formatDate, formatInt, formatMoney, formatPercent,
  isNegative } from '../../lib/format'
import { PeriodFilter, usePeriodParams } from './PeriodFilter'

export function BuyerDashboard({ type, id }: { type: BuyerType; id: string }) {
  const { params } = usePeriodParams()
  const [search, setSearch] = useSearchParams()
  const path = type === 'COMPANY' ? `/dashboard/companies/${id}` : `/dashboard/customers/${id}`
  const query = useQuery({ queryKey: ['dashboard', 'buyer', type, id, params], queryFn: () => api.get<BuyerDashboardData>(path, params) })
  const d = query.data

  const back = () => {
    const next = new URLSearchParams(search)
    next.delete('empresa')
    next.delete('cliente')
    setSearch(next)
  }
  const rows = (d?.daily ?? []) as unknown as Row[]
  const noSales = d ? d.quantity === 0 : true
  const historyLink = d
    ? `/historico?tipo=SALE&${type === 'COMPANY' ? 'empresa' : 'cliente'}=${id}&inicio=${d.period.start_date}&fim=${d.period.end_date}`
    : '/historico'
  const change = d?.comparison.revenue_change_percent ?? null

  return (
    <>
      <PageHeader title={d ? d.buyer.name : 'Carregando…'}
        subtitle={d ? `${BUYER_TYPE_LABELS[type]} · Período: ${formatDate(d.period.start_date)} a ${formatDate(d.period.end_date)}` : undefined}
        actions={<Button variant="secondary" onClick={back}>← Dashboard geral</Button>} />
      <div className="mb-5"><PeriodFilter /></div>
      {query.isLoading && <Loading />}
      {query.isError && <ErrorBox message={errorMessage(query.error)} />}
      {d && (
        <>
          <Card className="mb-6">
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <ActiveBadge active={d.buyer.is_active} />
              <span><span className="text-slate-500">Ciclo:</span> {BILLING_CYCLE_LABELS[d.buyer.billing_cycle]}</span>
              <span><span className="text-slate-500">Início:</span> {formatDate(d.buyer.start_date)}</span>
              <span><span className="text-slate-500">Data de pagamento:</span> {formatDate(d.buyer.payment_date)}</span>
              <Link to={historyLink} className="ml-auto text-brand-700 hover:underline">Fechamento do período no Histórico →</Link>
            </div>
          </Card>
          <div className="mb-6 grid grid-cols-5 gap-4">
            <Kpi label="Faturamento" emphasis value={formatMoney(d.revenue)}
              hint={`${formatPercent(d.revenue_share_percent)} da receita total`} />
            <Kpi label="Marmitas" value={formatInt(d.quantity)} hint={`${formatInt(d.sales_count)} venda(s)`} />
            <Kpi label="A receber" value={formatMoney(d.pending_revenue)}
              hint={<Link to={`${historyLink}&pagamento=PENDENTE`} className="text-brand-700 hover:underline">Ver vendas pendentes</Link>} />
            <Kpi label="Ticket médio" value={formatMoney(d.average_ticket)} hint={`Preço médio por marmita ${formatMoney(d.average_price_per_meal)}`} />
            <Kpi label="Variação vs. período anterior" value={change === null ? '—' : `${isNegative(change) ? '↓' : '↑'} ${formatPercent(change)}`}
              tone={change === null ? 'default' : isNegative(change) ? 'negative' : 'positive'}
              hint={`Anterior (${formatDate(d.comparison.previous_period.start_date)} a ${formatDate(d.comparison.previous_period.end_date)}): ${formatMoney(d.comparison.revenue)}`} />
          </div>
          <div className="mb-6 grid grid-cols-2 gap-6">
            <ChartCard title="Faturamento diário" rows={rows} xKey="date" xLabel="Data" empty={noSales}
              series={[{ key: 'revenue', label: 'Faturamento', color: COLORS.revenue }]}>
              <DailyBars rows={rows} series={[{ key: 'revenue', label: 'Faturamento', color: COLORS.revenue }]} />
            </ChartCard>
            <ChartCard title="Marmitas por dia" rows={rows} xKey="date" xLabel="Data" empty={noSales}
              series={[{ key: 'quantity', label: 'Marmitas', color: COLORS.quantity, kind: 'int' }]}>
              <DailyBars rows={rows} series={[{ key: 'quantity', label: 'Marmitas', color: COLORS.quantity, kind: 'int' }]} />
            </ChartCard>
          </div>
          <Card title="Últimas vendas do período" actions={<Link to={historyLink} className="text-sm text-brand-700 hover:underline">Ver todas no Histórico</Link>}>
            {d.recent_sales.length === 0 ? (
              <p className="text-sm text-slate-500">Nenhuma venda no período.</p>
            ) : (
              <Table>
                <thead><tr><Th>Data</Th><Th className="text-right">Qtd</Th><Th className="text-right">Preço</Th>
                  <Th className="text-right">Subtotal</Th><Th>Recebimento</Th><Th>Pagamento</Th><Th>Observações</Th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {d.recent_sales.map((s) => (
                    <tr key={s.id}>
                      <Td className="tabular">{formatDate(s.sale_date)}</Td>
                      <Td className="tabular text-right">{formatInt(s.quantity)}</Td>
                      <Td className="tabular text-right">{formatMoney(s.unit_price)}</Td>
                      <Td className="tabular text-right font-medium">{formatMoney(s.subtotal)}</Td>
                      <Td><DeliveryBadge type={s.delivery_type} /></Td>
                      <Td><PaymentBadge status={s.payment_status} /></Td>
                      <Td>{s.notes ?? '—'}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
            <p className="mt-3 text-xs text-slate-500">Somente faturamento: os custos são gerais do restaurante e entram apenas no lucro líquido geral.</p>
          </Card>
        </>
      )}
    </>
  )
}

