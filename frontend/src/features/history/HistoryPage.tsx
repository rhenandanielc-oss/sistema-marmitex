import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import { api, errorMessage } from '../../api/client'
import { useCategoryOptions, useCompanyOptions, useCustomerOptions } from '../../api/hooks'
import type { HistoryPage as HistoryPageData } from '../../api/types'
import { DeliveryBadge, PaymentBadge } from '../../components/badges'
import { Kpi } from '../../components/Kpi'
import { Badge, Button, Card, EmptyState, ErrorBox, Field, Input, Loading, PageHeader, Pagination, Select, Table, Td,
  Th } from '../../components/ui'
import { BUYER_TYPE_LABELS, COST_TYPE_LABELS, formatDate, formatInt, formatMoney, todayIso } from '../../lib/format'

/** Parâmetros da URL (pt-BR) → parâmetros da API. */
const URL_KEYS = {
  tipo: 'type', inicio: 'start_date', fim: 'end_date', comprador: 'buyer_type', empresa: 'company_id',
  cliente: 'customer_id', classificacao: 'cost_type', categoria: 'category_id', pagamento: 'payment_status',
  recebimento: 'delivery_type', ordem: 'sort', direcao: 'order',
  pagina: 'page',
} as const
type UrlKey = keyof typeof URL_KEYS

export function HistoryPage() {
  const [search, setSearch] = useSearchParams()
  const get = (key: UrlKey) => search.get(key) ?? ''
  const defaults: Partial<Record<UrlKey, string>> = { inicio: `${todayIso().slice(0, 8)}01`, fim: todayIso() }
  const value = (key: UrlKey) => (search.has(key) ? get(key) : defaults[key] ?? '')

  const setParam = (key: UrlKey, val: string) => {
    const next = new URLSearchParams(search)
    for (const k of Object.keys(defaults) as UrlKey[]) if (!next.has(k)) next.set(k, defaults[k]!)
    if (val) next.set(key, val)
    else next.delete(key)
    if (key !== 'pagina') next.delete('pagina')
    setSearch(next, { replace: true })
  }

  const params: Record<string, string> = { page_size: '20' }
  for (const k of Object.keys(URL_KEYS) as UrlKey[]) {
    const v = value(k)
    if (v) params[URL_KEYS[k]] = v
  }

  const history = useQuery({
    queryKey: ['history', 'list', params],
    queryFn: () => api.get<HistoryPageData>('/history', params),
    placeholderData: (prev) => prev,
  })
  const companies = useCompanyOptions(false)
  const customers = useCustomerOptions(false)
  const categories = useCategoryOptions(false)

  const sort = value('ordem') || 'date'
  const order = (value('direcao') || 'desc') as 'asc' | 'desc'
  const toggleSort = (key: 'date' | 'amount') => {
    const next = new URLSearchParams(search)
    next.set('ordem', key)
    next.set('direcao', sort === key && order === 'desc' ? 'asc' : 'desc')
    next.delete('pagina')
    setSearch(next, { replace: true })
  }
  const data = history.data
  const buyerFilter = !!(value('comprador') || value('empresa') || value('cliente') || value('pagamento') || value('recebimento'))

  return (
    <>
      <PageHeader title="Histórico" subtitle="Consulta de todas as vendas e custos lançados."
        actions={<Button variant="secondary" onClick={() => setSearch(new URLSearchParams(), { replace: true })}>Limpar filtros</Button>} />
      <Card className="mb-6">
        <div className="grid grid-cols-4 gap-4">
          <Field label="Lançamentos" htmlFor="h-type">
            <Select id="h-type" value={value('tipo')} onChange={(e) => setParam('tipo', e.target.value)}>
              <option value="">Vendas e custos</option>
              <option value="SALE">Somente vendas</option>
              <option value="COST">Somente custos</option>
            </Select>
          </Field>
          <Field label="Data inicial" htmlFor="h-start">
            <Input id="h-start" type="date" value={value('inicio')} onChange={(e) => setParam('inicio', e.target.value)} />
          </Field>
          <Field label="Data final" htmlFor="h-end">
            <Input id="h-end" type="date" value={value('fim')} onChange={(e) => setParam('fim', e.target.value)} />
          </Field>
          <Field label="Tipo de comprador" htmlFor="h-buyer">
            <Select id="h-buyer" value={value('comprador')} onChange={(e) => setParam('comprador', e.target.value)}>
              <option value="">Todos</option>
              <option value="COMPANY">Empresas</option>
              <option value="CUSTOMER">Clientes avulsos</option>
            </Select>
          </Field>
          <Field label="Empresa" htmlFor="h-company">
            <Select id="h-company" value={value('empresa')} onChange={(e) => setParam('empresa', e.target.value)}>
              <option value="">Todas</option>
              {(companies.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Field>
          <Field label="Cliente avulso" htmlFor="h-customer">
            <Select id="h-customer" value={value('cliente')} onChange={(e) => setParam('cliente', e.target.value)}>
              <option value="">Todos</option>
              {(customers.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Field>
          <Field label="Classificação do custo" htmlFor="h-ctype">
            <Select id="h-ctype" value={value('classificacao')} onChange={(e) => setParam('classificacao', e.target.value)}>
              <option value="">Todas</option>
              <option value="CUSTO_DIARIO">Diários</option>
              <option value="CUSTO_FIXO">Fixos</option>
            </Select>
          </Field>
          <Field label="Tipo de custo" htmlFor="h-cat">
            <Select id="h-cat" value={value('categoria')} onChange={(e) => setParam('categoria', e.target.value)}>
              <option value="">Todos</option>
              {(categories.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Field>
          <Field label="Pagamento" htmlFor="h-pay">
            <Select id="h-pay" value={value('pagamento')} onChange={(e) => setParam('pagamento', e.target.value)}>
              <option value="">Pagas e pendentes</option>
              <option value="PENDENTE">Pendentes (a receber)</option>
              <option value="PAGO">Pagas</option>
            </Select>
          </Field>
          <Field label="Recebimento" htmlFor="h-delivery">
            <Select id="h-delivery" value={value('recebimento')} onChange={(e) => setParam('recebimento', e.target.value)}>
              <option value="">Todos</option>
              <option value="OBRA">Obra</option>
              <option value="ENTREGA">Entrega</option>
              <option value="RETIRADA">Retirada</option>
            </Select>
          </Field>
        </div>
        {buyerFilter && (
          <p className="mt-3 text-xs text-slate-500">Com filtro de comprador, pagamento ou recebimento são exibidas apenas vendas — custos são gerais do restaurante.</p>
        )}
      </Card>

      {data && (
        <div className="mb-6 grid grid-cols-5 gap-4">
          <Kpi label="Total de vendas" value={formatMoney(data.totals.sales_total)} hint="Valor do fechamento do filtro" />
          <Kpi label="A receber" value={formatMoney(data.totals.sales_pending_total)} hint="Vendas pendentes de pagamento" />
          <Kpi label="Marmitas" value={formatInt(data.totals.sales_quantity)} hint={`${data.totals.sales_count} venda(s)`} />
          <Kpi label="Total de custos" value={formatMoney(data.totals.costs_total)} hint={`${data.totals.costs_count} custo(s)`} />
          <Kpi label="Lançamentos" value={formatInt(data.total)} />
        </div>
      )}

      <Card>
        {history.isLoading && <Loading />}
        {history.isError && <ErrorBox message={errorMessage(history.error)} />}
        {data && data.items.length === 0 && <EmptyState>Nenhum lançamento encontrado para os filtros.</EmptyState>}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <thead><tr>
                <Th sorted={sort === 'date' ? order : null} onClick={() => toggleSort('date')}>Data</Th>
                <Th>Lançamento</Th><Th>Descrição</Th><Th>Recebimento</Th><Th>Pagamento</Th><Th className="text-right">Qtd</Th><Th className="text-right">Preço</Th>
                <Th className="text-right" sorted={sort === 'amount' ? order : null} onClick={() => toggleSort('amount')}>Valor</Th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((item) => (
                  <tr key={`${item.kind}-${item.id}`}>
                    <Td className="tabular">{formatDate(item.date)}</Td>
                    <Td>{item.kind === 'SALE' ? <Badge tone="green">Venda</Badge> : <Badge tone="amber">Custo</Badge>}</Td>
                    <Td>
                      {item.sale && (<><span className="font-medium text-slate-900">{item.sale.buyer.name}</span>
                        <span className="ml-2 text-xs text-slate-500">{BUYER_TYPE_LABELS[item.sale.buyer.type]}</span></>)}
                      {item.cost && (<><span className="font-medium text-slate-900">{item.cost.category.name}</span>
                        <span className="ml-2 text-xs text-slate-500">{COST_TYPE_LABELS[item.cost.cost_type]}</span>
                        {item.cost.description && <div className="text-xs text-slate-500">{item.cost.description}</div>}</>)}
                    </Td>
                    <Td>{item.sale ? <DeliveryBadge type={item.sale.delivery_type} /> : '—'}</Td>
                    <Td>{item.sale ? <PaymentBadge status={item.sale.payment_status} /> : '—'}</Td>
                    <Td className="tabular text-right">{item.sale ? formatInt(item.sale.quantity) : '—'}</Td>
                    <Td className="tabular text-right">{item.sale ? formatMoney(item.sale.unit_price) : '—'}</Td>
                    <Td className={`tabular text-right font-medium ${item.kind === 'COST' ? 'text-red-700' : ''}`}>
                      {item.kind === 'COST' ? '− ' : ''}{formatMoney(item.amount)}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={data.page} pages={data.pages} total={data.total} onChange={(p) => setParam('pagina', String(p))} />
          </>
        )}
      </Card>
    </>
  )
}
