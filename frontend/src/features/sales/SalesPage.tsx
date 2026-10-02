import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { ApiError, api, errorMessage } from '../../api/client'
import { ENTRY_KEYS, useCompanyOptions, useCustomerOptions } from '../../api/hooks'
import type { BuyerType, HistoryPage, Page, Sale } from '../../api/types'
import { useToast } from '../../components/Toast'
import { Badge, Button, Card, ConfirmDialog, EmptyState, ErrorBox, Field, Input, Loading, Modal, PageHeader,
  Pagination, Select, Table, Td, Th } from '../../components/ui'
import { applyServerErrors } from '../../lib/forms'
import { BUYER_TYPE_LABELS, formatDate, formatInt, formatMoney, todayIso } from '../../lib/format'
import { MONEY_PATTERN, normalizeMoneyInput } from '../../lib/money'

const schema = z.object({
  buyer_type: z.enum(['COMPANY', 'CUSTOMER']),
  buyer_id: z.string().min(1, 'Selecione o comprador.'),
  unit_price: z.string().trim().regex(MONEY_PATTERN, 'Informe o preço (ex.: 18,50).'),
  quantity: z.string().trim().regex(/^\d+$/, 'Informe a quantidade (número inteiro).')
    .refine((v) => Number(v) > 0, 'A quantidade deve ser maior que zero.'),
  sale_date: z.string().min(1, 'Informe a data.'),
  notes: z.string().max(500),
})
type FormValues = z.infer<typeof schema>
const SERVER_FIELDS = ['unit_price', 'quantity', 'sale_date', 'notes', 'buyer_type']

function toBody(values: FormValues) {
  const id = Number(values.buyer_id)
  return {
    buyer_type: values.buyer_type,
    company_id: values.buyer_type === 'COMPANY' ? id : null,
    customer_id: values.buyer_type === 'CUSTOMER' ? id : null,
    unit_price: normalizeMoneyInput(values.unit_price),
    quantity: Number(values.quantity),
    sale_date: values.sale_date,
    notes: values.notes.trim() || null,
  }
}

function mapBuyerError(error: unknown, setError: (name: 'buyer_id', e: { message: string }) => void) {
  if (!(error instanceof ApiError)) return false
  const detail = error.details.find((d) => d.field === 'company_id' || d.field === 'customer_id')
  if (detail) setError('buyer_id', { message: detail.message })
  return !!detail
}

/** Campos do formulário de venda (usado no lançamento e na edição). */
function SaleFields({ form, sale, idPrefix }: {
  form: ReturnType<typeof useForm<FormValues>>
  sale?: Sale
  idPrefix: string
}) {
  const { register, control, setValue, formState: { errors } } = form
  const buyerType = useWatch({ control, name: 'buyer_type' }) as BuyerType
  const companies = useCompanyOptions(false)
  const customers = useCustomerOptions(false)
  const options = (buyerType === 'COMPANY' ? companies.data?.items : customers.data?.items) ?? []
  // Novos lançamentos: somente ativos. Na edição, mantém o comprador atual mesmo se desativado (R-VEN-7).
  const visible = options.filter((o) => o.is_active || (sale && sale.buyer.type === buyerType && sale.buyer.id === o.id))

  return (
    <div className="grid grid-cols-6 gap-4">
      <fieldset className="col-span-6 flex gap-6">
        <legend className="sr-only">Tipo de comprador</legend>
        {(['COMPANY', 'CUSTOMER'] as const).map((t) => (
          <label key={t} className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <input type="radio" value={t} {...register('buyer_type', { onChange: () => setValue('buyer_id', '') })} />
            {t === 'COMPANY' ? 'Empresa (empreiteira)' : 'Cliente avulso'}
          </label>
        ))}
      </fieldset>
      <div className="col-span-3">
        <Field label={buyerType === 'COMPANY' ? 'Empresa' : 'Cliente'} htmlFor={`${idPrefix}buyer`} error={errors.buyer_id?.message} required>
          <Select id={`${idPrefix}buyer`} {...register('buyer_id')}>
            <option value="">Selecione…</option>
            {visible.map((o) => (
              <option key={o.id} value={o.id}>{o.name}{o.location ? ` — ${o.location}` : ''}{o.is_active ? '' : ' (inativo)'}</option>
            ))}
          </Select>
        </Field>
      </div>
      <div className="col-span-1">
        <Field label="Preço unitário (R$)" htmlFor={`${idPrefix}price`} error={errors.unit_price?.message} required>
          <Input id={`${idPrefix}price`} inputMode="decimal" placeholder="0,00" {...register('unit_price')} />
        </Field>
      </div>
      <div className="col-span-1">
        <Field label="Quantidade" htmlFor={`${idPrefix}qty`} error={errors.quantity?.message} required>
          <Input id={`${idPrefix}qty`} inputMode="numeric" {...register('quantity')} />
        </Field>
      </div>
      <div className="col-span-1">
        <Field label="Data" htmlFor={`${idPrefix}date`} error={errors.sale_date?.message} required>
          <Input id={`${idPrefix}date`} type="date" max={todayIso()} {...register('sale_date')} />
        </Field>
      </div>
      <div className="col-span-6">
        <Field label="Observações" htmlFor={`${idPrefix}notes`} error={errors.notes?.message}>
          <Input id={`${idPrefix}notes`} {...register('notes')} />
        </Field>
      </div>
    </div>
  )
}

function useInvalidateEntries() {
  const queryClient = useQueryClient()
  return () => Promise.all(ENTRY_KEYS.map((key) => queryClient.invalidateQueries({ queryKey: [...key] })))
}

function NewSaleCard() {
  const notify = useToast()
  const invalidate = useInvalidateEntries()
  const [formError, setFormError] = useState<string | null>(null)
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { buyer_type: 'COMPANY', buyer_id: '', unit_price: '', quantity: '', sale_date: todayIso(), notes: '' },
  })
  const { handleSubmit, setError, setValue, getValues, reset, control, formState: { isSubmitting, dirtyFields } } = form
  const buyerType = useWatch({ control, name: 'buyer_type' })
  const buyerId = useWatch({ control, name: 'buyer_id' })

  // Sugere o preço da última venda para o mesmo comprador (apenas preenche o campo; o ADMIN pode alterar).
  const lastSale = useQuery({
    queryKey: ['sales', 'last', buyerType, buyerId],
    enabled: !!buyerId,
    queryFn: () => api.get<Page<Sale>>('/sales', {
      [buyerType === 'COMPANY' ? 'company_id' : 'customer_id']: buyerId, page_size: 1, sort: 'sale_date', order: 'desc',
    }),
  })
  useEffect(() => {
    const last = lastSale.data?.items[0]
    if (last && !dirtyFields.unit_price) setValue('unit_price', last.unit_price.replace('.', ','))
  }, [lastSale.data, dirtyFields.unit_price, setValue])

  async function onSubmit(values: FormValues) {
    setFormError(null)
    try {
      const sale = await api.post<Sale>('/sales', toBody(values))
      notify(`Venda registrada: ${sale.buyer.name} — ${formatInt(sale.quantity)} marmita(s), ${formatMoney(sale.subtotal)}.`)
      reset({ ...getValues(), quantity: '', notes: '' }, { keepDefaultValues: true })
      await invalidate()
    } catch (error) {
      const mapped = applyServerErrors(error, setError, SERVER_FIELDS) || mapBuyerError(error, setError)
      if (!mapped) setFormError(errorMessage(error))
    }
  }

  return (
    <Card title="Lançar venda" className="mb-6">
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <SaleFields form={form} idPrefix="new-" />
        {formError && <div className="mt-3"><ErrorBox message={formError} /></div>}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-slate-500">O subtotal é calculado pelo sistema ao salvar. A data pode ser alterada para lançar vendas esquecidas.</p>
          <Button type="submit" disabled={isSubmitting}>Registrar venda</Button>
        </div>
      </form>
    </Card>
  )
}

function EditSaleModal({ sale, onClose }: { sale: Sale; onClose: () => void }) {
  const notify = useToast()
  const invalidate = useInvalidateEntries()
  const [formError, setFormError] = useState<string | null>(null)
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      buyer_type: sale.buyer_type, buyer_id: String(sale.buyer.id), unit_price: sale.unit_price.replace('.', ','),
      quantity: String(sale.quantity), sale_date: sale.sale_date, notes: sale.notes ?? '',
    },
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    try {
      const updated = await api.patch<Sale>(`/sales/${sale.id}`, { ...toBody(values), version: sale.version })
      notify(`Venda atualizada: ${formatMoney(updated.subtotal)}.`)
      await invalidate()
      onClose()
    } catch (error) {
      const mapped = applyServerErrors(error, form.setError, SERVER_FIELDS) || mapBuyerError(error, form.setError)
      if (!mapped) setFormError(errorMessage(error))
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') { await invalidate(); onClose(); notify(error.message, 'error') }
    }
  }

  return (
    <Modal open wide title="Editar venda" onClose={onClose} footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button type="submit" form="edit-sale" disabled={form.formState.isSubmitting}>Salvar</Button>
      </>
    }>
      <form id="edit-sale" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <SaleFields form={form} sale={sale} idPrefix="edit-" />
        {formError && <div className="mt-3"><ErrorBox message={formError} /></div>}
      </form>
    </Modal>
  )
}

export function SalesPage() {
  const notify = useToast()
  const invalidate = useInvalidateEntries()
  const [filters, setFilters] = useState({ start_date: todayIso(), end_date: todayIso(), buyer_type: '' })
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<Sale | null>(null)
  const [deleting, setDeleting] = useState<Sale | null>(null)
  const params = { ...filters, page, page_size: 20 }

  const sales = useQuery({
    queryKey: ['sales', 'list', params],
    queryFn: () => api.get<Page<Sale>>('/sales', params),
    placeholderData: (prev) => prev,
  })
  const totals = useQuery({
    queryKey: ['history', 'sales-totals', filters],
    queryFn: () => api.get<HistoryPage>('/history', { ...filters, type: 'SALE', page_size: 1 }),
  })
  const remove = useMutation({
    mutationFn: (sale: Sale) => api.delete(`/sales/${sale.id}`),
    onSuccess: async () => { notify('Venda excluída.'); setDeleting(null); await invalidate() },
    onError: (error) => notify(errorMessage(error), 'error'),
  })

  const setFilter = (key: keyof typeof filters, value: string) => { setFilters((f) => ({ ...f, [key]: value })); setPage(1) }
  const t = totals.data?.totals

  return (
    <>
      <PageHeader title="Vendas" subtitle="Lançamento de vendas para empresas e clientes avulsos." />
      <NewSaleCard />
      <Card title="Vendas lançadas">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <Field label="De" htmlFor="f-start"><Input id="f-start" type="date" value={filters.start_date}
            onChange={(e) => setFilter('start_date', e.target.value)} /></Field>
          <Field label="Até" htmlFor="f-end"><Input id="f-end" type="date" value={filters.end_date}
            onChange={(e) => setFilter('end_date', e.target.value)} /></Field>
          <Field label="Comprador" htmlFor="f-type">
            <Select id="f-type" value={filters.buyer_type} onChange={(e) => setFilter('buyer_type', e.target.value)}>
              <option value="">Empresas e clientes</option>
              <option value="COMPANY">Somente empresas</option>
              <option value="CUSTOMER">Somente clientes avulsos</option>
            </Select>
          </Field>
          {t && (
            <div className="ml-auto flex gap-6 text-sm">
              <div><div className="text-slate-500">Marmitas</div><div className="tabular font-semibold">{formatInt(t.sales_quantity)}</div></div>
              <div><div className="text-slate-500">Total</div><div className="tabular font-semibold">{formatMoney(t.sales_total)}</div></div>
            </div>
          )}
        </div>
        {sales.isLoading && <Loading />}
        {sales.isError && <ErrorBox message={errorMessage(sales.error)} />}
        {sales.data && sales.data.items.length === 0 && <EmptyState>Nenhuma venda no período.</EmptyState>}
        {sales.data && sales.data.items.length > 0 && (
          <>
            <Table>
              <thead><tr>
                <Th>Data</Th><Th>Comprador</Th><Th className="text-right">Qtd</Th><Th className="text-right">Preço</Th>
                <Th className="text-right">Subtotal</Th><Th className="text-right">Ações</Th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {sales.data.items.map((s) => (
                  <tr key={s.id}>
                    <Td className="tabular">{formatDate(s.sale_date)}</Td>
                    <Td>
                      <span className="mr-2 font-medium text-slate-900">{s.buyer.name}</span>
                      <Badge tone={s.buyer_type === 'COMPANY' ? 'blue' : 'gray'}>{BUYER_TYPE_LABELS[s.buyer_type]}</Badge>
                      {s.notes && <div className="text-xs text-slate-500">{s.notes}</div>}
                    </Td>
                    <Td className="tabular text-right">{formatInt(s.quantity)}</Td>
                    <Td className="tabular text-right">{formatMoney(s.unit_price)}</Td>
                    <Td className="tabular text-right font-medium">{formatMoney(s.subtotal)}</Td>
                    <Td className="whitespace-nowrap text-right">
                      <Button variant="ghost" onClick={() => setEditing(s)}>Editar</Button>
                      <Button variant="ghost" className="text-red-600" onClick={() => setDeleting(s)}>Excluir</Button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={sales.data.page} pages={sales.data.pages} total={sales.data.total} onChange={setPage} />
          </>
        )}
      </Card>
      {editing && <EditSaleModal sale={editing} onClose={() => setEditing(null)} />}
      <ConfirmDialog open={!!deleting} title="Excluir venda" danger confirmLabel="Excluir" busy={remove.isPending}
        message={deleting && `Excluir a venda de ${formatDate(deleting.sale_date)} para ${deleting.buyer.name} (${formatMoney(deleting.subtotal)})?`}
        onCancel={() => setDeleting(null)} onConfirm={() => deleting && remove.mutate(deleting)} />
    </>
  )
}
