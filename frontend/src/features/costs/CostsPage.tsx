import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError, api, errorMessage } from '../../api/client'
import { ENTRY_KEYS, useCategoryOptions } from '../../api/hooks'
import type { Cost, CostPage, CostSummary } from '../../api/types'
import { Kpi } from '../../components/Kpi'
import { useToast } from '../../components/Toast'
import { Badge, Button, Card, ConfirmDialog, EmptyState, ErrorBox, Field, Input, Loading, Modal, PageHeader,
  Pagination, Select, Table, Td, Th } from '../../components/ui'
import { applyServerErrors } from '../../lib/forms'
import { COST_TYPE_LABELS, formatDate, formatMoney, todayIso } from '../../lib/format'
import { MONEY_PATTERN, normalizeMoneyInput } from '../../lib/money'

const schema = z.object({
  category_id: z.string().min(1, 'Selecione o tipo de custo.'),
  amount: z.string().trim().regex(MONEY_PATTERN, 'Informe o valor (ex.: 150,00).'),
  cost_date: z.string().min(1, 'Informe a data.'),
  description: z.string().max(500),
})
type FormValues = z.infer<typeof schema>
const SERVER_FIELDS = ['category_id', 'amount', 'cost_date', 'description']

function firstDayOfMonth(): string {
  return `${todayIso().slice(0, 8)}01`
}

function useInvalidateEntries() {
  const queryClient = useQueryClient()
  return () => Promise.all(ENTRY_KEYS.map((key) => queryClient.invalidateQueries({ queryKey: [...key] })))
}

function CostForm({ cost, onDone, idPrefix }: { cost?: Cost; onDone?: () => void; idPrefix: string }) {
  const notify = useToast()
  const invalidate = useInvalidateEntries()
  const categories = useCategoryOptions(false)
  const [formError, setFormError] = useState<string | null>(null)
  const { register, handleSubmit, setError, reset, getValues, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      category_id: cost ? String(cost.category.id) : '', amount: cost ? cost.amount.replace('.', ',') : '',
      cost_date: cost?.cost_date ?? todayIso(), description: cost?.description ?? '',
    },
  })
  const all = categories.data?.items ?? []
  // Novos custos: somente tipos ativos. Na edição, mantém o tipo atual mesmo se desativado (R-CUS-2).
  const visible = all.filter((c) => c.is_active || c.id === cost?.category.id)

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const category = all.find((c) => String(c.id) === values.category_id)
    const body = {
      category_id: Number(values.category_id),
      cost_type: category?.cost_type,
      amount: normalizeMoneyInput(values.amount),
      cost_date: values.cost_date,
      description: values.description.trim() || null,
    }
    try {
      if (cost) {
        await api.patch<Cost>(`/costs/${cost.id}`, { ...body, version: cost.version })
        notify('Custo atualizado.')
      } else {
        const created = await api.post<Cost>('/costs', body)
        notify(`Custo registrado: ${created.category.name} — ${formatMoney(created.amount)}.`)
        reset({ ...getValues(), amount: '', description: '' })
      }
      await invalidate()
      onDone?.()
    } catch (error) {
      if (!applyServerErrors(error, setError, SERVER_FIELDS)) setFormError(errorMessage(error))
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') { await invalidate(); onDone?.() }
    }
  }

  const group = (type: string) => visible.filter((c) => c.cost_type === type)
  return (
    <form id={`${idPrefix}cost-form`} onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className="grid grid-cols-6 gap-4">
        <div className="col-span-2">
          <Field label="Tipo de custo" htmlFor={`${idPrefix}category`} error={errors.category_id?.message} required>
            <Select id={`${idPrefix}category`} {...register('category_id')}>
              <option value="">Selecione…</option>
              <optgroup label="Custos diários">
                {group('CUSTO_DIARIO').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
              <optgroup label="Custos fixos">
                {group('CUSTO_FIXO').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
            </Select>
          </Field>
        </div>
        <div className="col-span-1">
          <Field label="Valor (R$)" htmlFor={`${idPrefix}amount`} error={errors.amount?.message} required>
            <Input id={`${idPrefix}amount`} inputMode="decimal" placeholder="0,00" {...register('amount')} />
          </Field>
        </div>
        <div className="col-span-1">
          <Field label="Data" htmlFor={`${idPrefix}date`} error={errors.cost_date?.message} required>
            <Input id={`${idPrefix}date`} type="date" max={todayIso()} {...register('cost_date')} />
          </Field>
        </div>
        <div className="col-span-2">
          <Field label="Descrição" htmlFor={`${idPrefix}description`} error={errors.description?.message}>
            <Input id={`${idPrefix}description`} {...register('description')} />
          </Field>
        </div>
      </div>
      {formError && <div className="mt-3"><ErrorBox message={formError} /></div>}
      {!cost && (
        <div className="mt-4 flex justify-end">
          <Button type="submit" disabled={isSubmitting}>Registrar custo</Button>
        </div>
      )}
    </form>
  )
}

function MonthTotals() {
  const summary = useQuery({ queryKey: ['costs', 'summary', 'month'], queryFn: () => api.get<CostSummary>('/costs/summary') })
  const s = summary.data
  return (
    <div className="mb-6 grid grid-cols-3 gap-4">
      <Kpi label="Custos diários no mês" value={formatMoney(s?.daily_costs)} />
      <Kpi label="Custos fixos no mês" value={formatMoney(s?.fixed_costs)} />
      <Kpi label="Custos totais no mês" value={formatMoney(s?.total_costs)} emphasis
        hint={s && `${formatDate(s.period.start_date)} a ${formatDate(s.period.end_date)} · ${s.count} lançamento(s)`} />
    </div>
  )
}

export function CostsPage() {
  const notify = useToast()
  const invalidate = useInvalidateEntries()
  const categories = useCategoryOptions(false)
  const [filters, setFilters] = useState({ start_date: firstDayOfMonth(), end_date: todayIso(), cost_type: '', category_id: '' })
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<Cost | null>(null)
  const [deleting, setDeleting] = useState<Cost | null>(null)
  const params = { ...filters, sort: 'cost_date', order, page, page_size: 20 }

  const costs = useQuery({
    queryKey: ['costs', 'list', params],
    queryFn: () => api.get<CostPage>('/costs', params),
    placeholderData: (prev) => prev,
  })
  const remove = useMutation({
    mutationFn: (cost: Cost) => api.delete(`/costs/${cost.id}`),
    onSuccess: async () => { notify('Custo excluído.'); setDeleting(null); await invalidate() },
    onError: (error) => notify(errorMessage(error), 'error'),
  })
  const setFilter = (key: keyof typeof filters, value: string) => { setFilters((f) => ({ ...f, [key]: value })); setPage(1) }
  const data = costs.data

  return (
    <>
      <PageHeader title="Custos" subtitle="Custos gerais do restaurante. O total vai somando a cada novo lançamento." />
      <MonthTotals />
      <Card title="Lançar custo" className="mb-6"><CostForm idPrefix="new-" /></Card>
      <Card title="Custos lançados">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <Field label="De" htmlFor="c-start"><Input id="c-start" type="date" value={filters.start_date}
            onChange={(e) => setFilter('start_date', e.target.value)} /></Field>
          <Field label="Até" htmlFor="c-end"><Input id="c-end" type="date" value={filters.end_date}
            onChange={(e) => setFilter('end_date', e.target.value)} /></Field>
          <Field label="Classificação" htmlFor="c-type">
            <Select id="c-type" value={filters.cost_type} onChange={(e) => setFilter('cost_type', e.target.value)}>
              <option value="">Diários e fixos</option>
              <option value="CUSTO_DIARIO">Diários</option>
              <option value="CUSTO_FIXO">Fixos</option>
            </Select>
          </Field>
          <Field label="Tipo de custo" htmlFor="c-cat">
            <Select id="c-cat" value={filters.category_id} onChange={(e) => setFilter('category_id', e.target.value)}>
              <option value="">Todos</option>
              {(categories.data?.items ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </Select>
          </Field>
          {data && (
            <div className="ml-auto flex gap-6 text-sm">
              <div><div className="text-slate-500">Diários</div><div className="tabular font-semibold">{formatMoney(data.totals.daily_costs)}</div></div>
              <div><div className="text-slate-500">Fixos</div><div className="tabular font-semibold">{formatMoney(data.totals.fixed_costs)}</div></div>
              <div><div className="text-slate-500">Total do filtro</div><div className="tabular font-semibold">{formatMoney(data.totals.total_costs)}</div></div>
            </div>
          )}
        </div>
        {costs.isLoading && <Loading />}
        {costs.isError && <ErrorBox message={errorMessage(costs.error)} />}
        {data && data.items.length === 0 && <EmptyState>Nenhum custo no período.</EmptyState>}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <thead><tr>
                <Th sorted={order} onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')}>Data</Th>
                <Th>Tipo de custo</Th><Th>Classificação</Th><Th>Descrição</Th>
                <Th className="text-right">Valor</Th><Th className="text-right">Acumulado</Th><Th className="text-right">Ações</Th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <Td className="tabular">{formatDate(c.cost_date)}</Td>
                    <Td className="font-medium text-slate-900">{c.category.name}</Td>
                    <Td><Badge tone={c.cost_type === 'CUSTO_FIXO' ? 'amber' : 'blue'}>{COST_TYPE_LABELS[c.cost_type]}</Badge></Td>
                    <Td>{c.description ?? '—'}</Td>
                    <Td className="tabular text-right">{formatMoney(c.amount)}</Td>
                    <Td className="tabular text-right font-medium">{formatMoney(c.running_total)}</Td>
                    <Td className="whitespace-nowrap text-right">
                      <Button variant="ghost" onClick={() => setEditing(c)}>Editar</Button>
                      <Button variant="ghost" className="text-red-600" onClick={() => setDeleting(c)}>Excluir</Button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
          </>
        )}
      </Card>
      {editing && (
        <Modal open wide title="Editar custo" onClose={() => setEditing(null)} footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>Cancelar</Button>
            <Button type="submit" form="edit-cost-form">Salvar</Button>
          </>
        }>
          <CostForm cost={editing} idPrefix="edit-" onDone={() => setEditing(null)} />
        </Modal>
      )}
      <ConfirmDialog open={!!deleting} title="Excluir custo" danger confirmLabel="Excluir" busy={remove.isPending}
        message={deleting && `Excluir o custo "${deleting.category.name}" de ${formatDate(deleting.cost_date)} (${formatMoney(deleting.amount)})?`}
        onCancel={() => setDeleting(null)} onConfirm={() => deleting && remove.mutate(deleting)} />
    </>
  )
}
