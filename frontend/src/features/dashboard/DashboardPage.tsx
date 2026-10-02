import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { api, errorMessage } from '../../api/client'
import { useCompanyOptions, useCustomerOptions } from '../../api/hooks'
import type { ByBuyer, Daily, SalesByCompanyDaily, Summary } from '../../api/types'
import { ChartCard, COLORS, DailyBars, DailyLines, RankingBars, SERIES, type Row, type SeriesSpec } from '../../components/charts'
import { Kpi } from '../../components/Kpi'
import { Card, ErrorBox, Loading, PageHeader, Select, Table, Td, Th } from '../../components/ui'
import { BUYER_TYPE_LABELS, formatDate, formatInt, formatMoney, formatPercent, isNegative } from '../../lib/format'
import { BuyerDashboard } from './BuyerDashboard'
import { PeriodFilter, usePeriodParams } from './PeriodFilter'

function BuyerPicker() {
  const [search, setSearch] = useSearchParams()
  const companies = useCompanyOptions(false)
  const customers = useCustomerOptions(false)
  const open = (key: 'empresa' | 'cliente', id: string) => {
    if (!id) return
    const next = new URLSearchParams(search)
    next.delete('empresa')
    next.delete('cliente')
    next.set(key, id)
    setSearch(next)
  }
  return (
    <div className="flex gap-2">
      <Select aria-label="Ver empresa" value="" onChange={(e) => open('empresa', e.target.value)}>
        <option value="">Ver empresa…</option>
        {(companies.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </Select>
      <Select aria-label="Ver cliente" value="" onChange={(e) => open('cliente', e.target.value)}>
        <option value="">Ver cliente avulso…</option>
        {(customers.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </Select>
    </div>
  )
}

function SummaryKpis({ s }: { s: Summary }) {
  return (
    <div className="mb-6 grid grid-cols-4 gap-4">
      <Kpi label="Lucro líquido" emphasis value={formatMoney(s.net_profit)} tone={isNegative(s.net_profit) ? 'negative' : 'positive'}
        hint={`Margem ${formatPercent(s.net_margin_percent)} · receita − todos os custos`} />
      <Kpi label="Receita total" value={formatMoney(s.revenue)}
        hint={`Empresas ${formatMoney(s.revenue_by_buyer_type.COMPANY)} · Clientes ${formatMoney(s.revenue_by_buyer_type.CUSTOMER)}`} />
      <Kpi label="Custos totais" value={formatMoney(s.total_costs)}
        hint={`Fixos ${formatMoney(s.fixed_costs)} · Diários ${formatMoney(s.daily_costs)}`} />
      <Kpi label="Quantidade de marmitas" value={formatInt(s.quantity)}
        hint={`Empresas ${formatInt(s.quantity_by_buyer_type.COMPANY)} · Clientes ${formatInt(s.quantity_by_buyer_type.CUSTOMER)}`} />
      <Kpi label="Custos fixos" value={formatMoney(s.fixed_costs)} />
      <Kpi label="Custos diários" value={formatMoney(s.daily_costs)} />
      <Kpi label="Custo médio por marmita" value={formatMoney(s.average_cost_per_meal)}
        hint={s.average_cost_per_meal === null ? 'Sem marmitas no período' : 'Custos totais ÷ marmitas'} />
      <Kpi label="Ticket médio" value={formatMoney(s.average_ticket)}
        hint={s.average_ticket === null ? 'Sem vendas no período' : `${formatInt(s.sales_count)} venda(s) · preço médio ${formatMoney(s.average_price_per_meal)}`} />
    </div>
  )
}

function RevenueByBuyer({ data }: { data: ByBuyer }) {
  const companies = data.items.filter((i) => i.buyer.type === 'COMPANY')
  const chartRows: Row[] = companies.slice(0, 12).map((i) => ({ name: i.buyer.name, revenue: i.revenue }))
  return (
    <div className="grid grid-cols-5 gap-6">
      <div className="col-span-2">
      <ChartCard title="Receita por empresa" subtitle="12 maiores" rows={chartRows} xKey="name" xLabel="Empresa"
        series={[{ key: 'revenue', label: 'Receita', color: COLORS.revenue }]} empty={companies.length === 0}>
        <RankingBars rows={chartRows} valueKey="revenue" labelKey="name" label="Receita" />
      </ChartCard>
      </div>
      <Card title="Faturamento por empresa e cliente" className="col-span-3">
        <div className="max-h-64 overflow-y-auto">
          <Table>
            <thead><tr><Th>Comprador</Th><Th className="text-right">Faturamento</Th><Th className="text-right">Marmitas</Th>
              <Th className="text-right">Ticket médio</Th><Th className="text-right">%</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((i) => (
                <tr key={`${i.buyer.type}-${i.buyer.id}`}>
                  <Td>
                    <Link className="font-medium text-brand-700 hover:underline"
                      to={`/dashboard?${i.buyer.type === 'COMPANY' ? 'empresa' : 'cliente'}=${i.buyer.id}`}>{i.buyer.name}</Link>
                    <span className="ml-2 text-xs text-slate-500">{BUYER_TYPE_LABELS[i.buyer.type]}</span>
                  </Td>
                  <Td className="tabular text-right">{formatMoney(i.revenue)}</Td>
                  <Td className="tabular text-right">{formatInt(i.quantity)}</Td>
                  <Td className="tabular text-right">{formatMoney(i.average_ticket)}</Td>
                  <Td className="tabular text-right">{formatPercent(i.revenue_share_percent)}</Td>
                </tr>
              ))}
              {data.items.length === 0 && <tr><Td className="text-center text-slate-500">Sem vendas no período.</Td></tr>}
            </tbody>
            {data.items.length > 0 && (
              <tfoot className="border-t-2 border-slate-200 text-sm font-medium">
                {(['COMPANY', 'CUSTOMER'] as const).map((t) => (
                  <tr key={t}><Td>Subtotal {t === 'COMPANY' ? 'empresas' : 'clientes avulsos'}</Td>
                    <Td className="tabular text-right">{formatMoney(data.subtotals[t].revenue)}</Td>
                    <Td className="tabular text-right">{formatInt(data.subtotals[t].quantity)}</Td><Td /><Td /></tr>
                ))}
                <tr><Td className="font-semibold">Total</Td><Td className="tabular text-right font-semibold">{formatMoney(data.revenue)}</Td>
                  <Td /><Td /><Td /></tr>
              </tfoot>
            )}
          </Table>
        </div>
      </Card>
    </div>
  )
}

function CompanyHistory({ data }: { data: SalesByCompanyDaily }) {
  const series: SeriesSpec[] = data.companies.map((c, i) => ({ key: `c${c.id}`, label: c.name, color: SERIES[i] }))
  if (data.has_other_companies) series.push({ key: 'others', label: 'Outras empresas', color: SERIES[6] })
  series.push({ key: 'customers', label: 'Clientes avulsos', color: SERIES[7] })
  const rows: Row[] = data.items.map((item) => {
    const row: Row = { date: item.date, others: item.other_companies, customers: item.customers }
    for (const c of data.companies) row[`c${c.id}`] = item.values[String(c.id)]
    return row
  })
  return (
    <ChartCard title="Histórico de vendas por empresa" subtitle="receita diária por comprador — 6 maiores empresas, demais agrupadas"
      rows={rows} series={series} xKey="date" xLabel="Data"
      empty={data.companies.length === 0 && rows.every((r) => Number(r.customers) === 0)}>
      <DailyBars stacked rows={rows} series={series} />
    </ChartCard>
  )
}

function GeneralDashboard() {
  const { params } = usePeriodParams()
  const summary = useQuery({ queryKey: ['dashboard', 'summary', params], queryFn: () => api.get<Summary>('/dashboard/summary', params) })
  const daily = useQuery({ queryKey: ['dashboard', 'daily', params], queryFn: () => api.get<Daily>('/dashboard/daily', params) })
  const byBuyer = useQuery({ queryKey: ['dashboard', 'by-buyer', params], queryFn: () => api.get<ByBuyer>('/dashboard/by-buyer', params) })
  const companies = useQuery({
    queryKey: ['dashboard', 'companies-daily', params],
    queryFn: () => api.get<SalesByCompanyDaily>('/dashboard/sales-by-company-daily', { ...params, top: 6 }),
  })

  const error = summary.error ?? daily.error
  const rows: Row[] = (daily.data?.items ?? []) as unknown as Row[]
  const noSales = daily.data?.items.every((d) => d.quantity === 0) ?? true
  const noCosts = daily.data?.items.every((d) => Number(d.total_costs) === 0) ?? true
  const period = summary.data?.period

  return (
    <>
      <PageHeader title="Dashboard"
        subtitle={period ? `Período: ${formatDate(period.start_date)} a ${formatDate(period.end_date)} (${period.days} dia(s))` : ' '}
        actions={<BuyerPicker />} />
      <div className="mb-5"><PeriodFilter /></div>
      {error && <ErrorBox message={errorMessage(error)} />}
      {summary.isLoading && <Loading />}
      {summary.data && <SummaryKpis s={summary.data} />}
      {daily.data && (
        <div className="flex flex-col gap-6">
          <ChartCard title="Acumulado no período" subtitle="receita, custos e lucro líquido somados dia a dia" rows={rows}
            xKey="date" xLabel="Data" empty={noSales && noCosts}
            series={[
              { key: 'cumulative_revenue', label: 'Receita acumulada', color: COLORS.revenue },
              { key: 'cumulative_costs', label: 'Custos acumulados', color: COLORS.costs },
              { key: 'cumulative_net_profit', label: 'Lucro acumulado', color: COLORS.profit },
            ]}>
            <DailyLines rows={rows} series={[
              { key: 'cumulative_revenue', label: 'Receita acumulada', color: COLORS.revenue },
              { key: 'cumulative_costs', label: 'Custos acumulados', color: COLORS.costs },
              { key: 'cumulative_net_profit', label: 'Lucro acumulado', color: COLORS.profit },
            ]} />
          </ChartCard>
          <div className="grid grid-cols-2 gap-6">
            <ChartCard title="Receita diária" rows={rows} xKey="date" xLabel="Data" empty={noSales}
              series={[{ key: 'revenue', label: 'Receita', color: COLORS.revenue }]}>
              <DailyBars rows={rows} series={[{ key: 'revenue', label: 'Receita', color: COLORS.revenue }]} />
            </ChartCard>
            <ChartCard title="Quantidade diária de marmitas" rows={rows} xKey="date" xLabel="Data" empty={noSales}
              series={[{ key: 'quantity', label: 'Marmitas', color: COLORS.quantity, kind: 'int' }]}>
              <DailyBars rows={rows} series={[{ key: 'quantity', label: 'Marmitas', color: COLORS.quantity, kind: 'int' }]} />
            </ChartCard>
            <ChartCard title="Custos diários" subtitle="diários e fixos" rows={rows} xKey="date" xLabel="Data" empty={noCosts}
              series={[
                { key: 'daily_costs', label: 'Custos diários', color: COLORS.dailyCosts },
                { key: 'fixed_costs', label: 'Custos fixos', color: COLORS.fixedCosts },
              ]}>
              <DailyBars stacked rows={rows} series={[
                { key: 'daily_costs', label: 'Custos diários', color: COLORS.dailyCosts },
                { key: 'fixed_costs', label: 'Custos fixos', color: COLORS.fixedCosts },
              ]} />
            </ChartCard>
            <ChartCard title="Lucro diário" subtitle="dias com custo fixo podem ficar negativos" rows={rows} xKey="date"
              xLabel="Data" empty={noSales && noCosts}
              series={[{ key: 'net_profit', label: 'Lucro do dia', color: COLORS.positive }]}>
              <DailyBars signed rows={rows} series={[{ key: 'net_profit', label: 'Lucro do dia', color: COLORS.positive }]} />
            </ChartCard>
          </div>
          {byBuyer.data && <RevenueByBuyer data={byBuyer.data} />}
          {companies.data && <CompanyHistory data={companies.data} />}
        </div>
      )}
    </>
  )
}

export function DashboardPage() {
  const [search] = useSearchParams()
  const company = search.get('empresa')
  const customer = search.get('cliente')
  if (company) return <BuyerDashboard type="COMPANY" id={company} />
  if (customer) return <BuyerDashboard type="CUSTOMER" id={customer} />
  return <GeneralDashboard />
}

