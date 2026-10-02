import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'

import { ApiError, errorMessage } from '../../api/client'
import type { Customer } from '../../api/types'
import { useToast } from '../../components/Toast'
import { ActiveBadge, Button, Card, EmptyState, ErrorBox, Field, Input, Loading, Modal, PageHeader, Pagination,
  Select, Table, Td, Textarea, Th } from '../../components/ui'
import { applyServerErrors, blankToNull } from '../../lib/forms'
import { BILLING_CYCLE_LABELS, formatDate } from '../../lib/format'
import { useRegistry, useSaveRegistry } from '../registry'

const schema = z.object({
  name: z.string().trim().min(2, 'Informe o nome (mínimo 2 caracteres).').max(150),
  phone: z.string().max(20),
  document: z.string().max(18),
  location: z.string().max(150),
  billing_cycle: z.enum(['A_VISTA', 'SEMANAL', 'QUINZENAL', 'MENSAL']),
  start_date: z.string(),
  payment_date: z.string(),
  notes: z.string().max(2000),
})
type FormValues = z.infer<typeof schema>
const FIELDS = Object.keys(schema.shape)

function toForm(c?: Customer): FormValues {
  return {
    name: c?.name ?? '', phone: c?.phone ?? '', document: c?.document ?? '', location: c?.location ?? '',
    billing_cycle: c?.billing_cycle ?? 'MENSAL', start_date: c?.start_date ?? '', payment_date: c?.payment_date ?? '',
    notes: c?.notes ?? '',
  }
}

function CustomerForm({ customer, onClose }: { customer?: Customer; onClose: () => void }) {
  const notify = useToast()
  const save = useSaveRegistry<Customer>('customers')
  const [formError, setFormError] = useState<string | null>(null)
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema), defaultValues: toForm(customer),
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const body: Record<string, unknown> = blankToNull(values)
    if (customer) body.version = customer.version
    try {
      await save.mutateAsync({ id: customer?.id, body })
      notify(customer ? 'Cliente atualizado.' : 'Cliente cadastrado.')
      onClose()
    } catch (error) {
      if (!applyServerErrors(error, setError, FIELDS)) setFormError(errorMessage(error))
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') onClose()
    }
  }

  return (
    <Modal open title={customer ? 'Editar cliente avulso' : 'Novo cliente avulso'} onClose={onClose} wide footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button type="submit" form="customer-form" disabled={isSubmitting}>Salvar</Button>
      </>
    }>
      <form id="customer-form" onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-4" noValidate>
        <div className="col-span-2">
          <Field label="Nome" htmlFor="name" error={errors.name?.message} required>
            <Input id="name" {...register('name')} autoFocus />
          </Field>
        </div>
        <Field label="Telefone" htmlFor="phone" error={errors.phone?.message}>
          <Input id="phone" {...register('phone')} />
        </Field>
        <Field label="CPF ou CNPJ" htmlFor="document" error={errors.document?.message} hint="Opcional.">
          <Input id="document" {...register('document')} />
        </Field>
        <div className="col-span-2">
          <Field label="Local / obra" htmlFor="location" error={errors.location?.message}>
            <Input id="location" {...register('location')} />
          </Field>
        </div>
        <Field label="Ciclo de pagamento" htmlFor="billing_cycle" error={errors.billing_cycle?.message} required>
          <Select id="billing_cycle" {...register('billing_cycle')}>
            <option value="A_VISTA">À vista</option>
            <option value="SEMANAL">Semanal</option>
            <option value="QUINZENAL">Quinzenal</option>
            <option value="MENSAL">Mensal</option>
          </Select>
        </Field>
        <div />
        <Field label="Data de início" htmlFor="start_date" error={errors.start_date?.message}>
          <Input id="start_date" type="date" {...register('start_date')} />
        </Field>
        <Field label="Data de pagamento" htmlFor="payment_date" error={errors.payment_date?.message}>
          <Input id="payment_date" type="date" {...register('payment_date')} />
        </Field>
        <div className="col-span-2">
          <Field label="Observações" htmlFor="notes" error={errors.notes?.message}>
            <Textarea id="notes" {...register('notes')} />
          </Field>
        </div>
        {formError && <div className="col-span-2"><ErrorBox message={formError} /></div>}
      </form>
    </Modal>
  )
}

export function CustomersPage() {
  const r = useRegistry<Customer>('customers', 'Cliente')
  const [editing, setEditing] = useState<Customer | 'new' | null>(null)
  const data = r.list.data

  return (
    <>
      <PageHeader title="Clientes avulsos" subtitle="Compradores independentes das empresas (ex.: trabalhador da obra que paga no mês)."
        actions={<Button onClick={() => setEditing('new')}>Novo cliente</Button>} />
      <Card>
        <div className="mb-4 flex flex-wrap gap-3">
          <Input aria-label="Pesquisar" placeholder="Pesquisar por nome, telefone ou local…" value={r.q}
            onChange={(e) => r.setQ(e.target.value)} className="w-80" />
          <Select aria-label="Situação" value={r.active} onChange={(e) => r.setActive(e.target.value as '' | 'true' | 'false')}>
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </div>
        {r.list.isLoading && <Loading />}
        {r.list.isError && <ErrorBox message={errorMessage(r.list.error)} />}
        {data && data.items.length === 0 && <EmptyState>Nenhum cliente encontrado.</EmptyState>}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <thead><tr>
                <Th>Nome</Th><Th>Telefone</Th><Th>Local / obra</Th><Th>Ciclo</Th><Th>Início</Th><Th>Pagamento</Th>
                <Th>Situação</Th><Th className="text-right">Ações</Th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <Td className="font-medium text-slate-900">{c.name}</Td>
                    <Td>{c.phone ?? '—'}</Td>
                    <Td>{c.location ?? '—'}</Td>
                    <Td>{BILLING_CYCLE_LABELS[c.billing_cycle]}</Td>
                    <Td className="tabular">{formatDate(c.start_date)}</Td>
                    <Td className="tabular">{formatDate(c.payment_date)}</Td>
                    <Td><ActiveBadge active={c.is_active} /></Td>
                    <Td className="whitespace-nowrap text-right">
                      <Link to={`/dashboard?cliente=${c.id}`} className="mr-2 text-sm text-brand-600 hover:underline">Dashboard</Link>
                      <Button variant="ghost" onClick={() => setEditing(c)}>Editar</Button>
                      <Button variant="ghost" onClick={() => r.toggle.mutate(c)} disabled={r.toggle.isPending}>
                        {c.is_active ? 'Desativar' : 'Ativar'}
                      </Button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={data.page} pages={data.pages} total={data.total} onChange={r.setPage} />
          </>
        )}
      </Card>
      {editing && <CustomerForm customer={editing === 'new' ? undefined : editing} onClose={() => setEditing(null)} />}
    </>
  )
}
