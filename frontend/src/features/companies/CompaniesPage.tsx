import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'

import { ApiError, errorMessage } from '../../api/client'
import type { Company } from '../../api/types'
import { useToast } from '../../components/Toast'
import { ActiveBadge, Button, Card, EmptyState, ErrorBox, Field, Input, Loading, Modal, PageHeader, Pagination,
  Select, Table, Td, Textarea, Th } from '../../components/ui'
import { applyServerErrors, blankToNull } from '../../lib/forms'
import { BILLING_CYCLE_LABELS, formatCnpj, formatDate } from '../../lib/format'
import { useRegistry, useSaveRegistry } from '../registry'

const schema = z.object({
  name: z.string().trim().min(2, 'Informe o nome (mínimo 2 caracteres).').max(150),
  trade_name: z.string().max(150),
  cnpj: z.string().max(18),
  location: z.string().max(150),
  contact_name: z.string().max(120),
  phone: z.string().max(20),
  email: z.string().max(254).refine((v) => v === '' || /^\S+@\S+\.\S+$/.test(v), 'E-mail inválido.'),
  billing_cycle: z.enum(['QUINZENAL', 'MENSAL']),
  start_date: z.string(),
  payment_date: z.string(),
  notes: z.string().max(2000),
})
type FormValues = z.infer<typeof schema>
const FIELDS = Object.keys(schema.shape)

function toForm(c?: Company): FormValues {
  return {
    name: c?.name ?? '', trade_name: c?.trade_name ?? '', cnpj: c?.cnpj ?? '', location: c?.location ?? '',
    contact_name: c?.contact_name ?? '', phone: c?.phone ?? '', email: c?.email ?? '',
    billing_cycle: c?.billing_cycle ?? 'MENSAL', start_date: c?.start_date ?? '', payment_date: c?.payment_date ?? '',
    notes: c?.notes ?? '',
  }
}

function CompanyForm({ company, onClose }: { company?: Company; onClose: () => void }) {
  const notify = useToast()
  const save = useSaveRegistry<Company>('companies')
  const [formError, setFormError] = useState<string | null>(null)
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema), defaultValues: toForm(company),
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const body: Record<string, unknown> = blankToNull(values)
    if (company) body.version = company.version
    try {
      await save.mutateAsync({ id: company?.id, body })
      notify(company ? 'Empresa atualizada.' : 'Empresa cadastrada.')
      onClose()
    } catch (error) {
      if (!applyServerErrors(error, setError, FIELDS)) setFormError(errorMessage(error))
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') onClose()
    }
  }

  return (
    <Modal open title={company ? 'Editar empresa' : 'Nova empresa'} onClose={onClose} wide footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button type="submit" form="company-form" disabled={isSubmitting}>Salvar</Button>
      </>
    }>
      <form id="company-form" onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-4" noValidate>
        <div className="col-span-2">
          <Field label="Nome (razão social)" htmlFor="name" error={errors.name?.message} required>
            <Input id="name" {...register('name')} autoFocus />
          </Field>
        </div>
        <Field label="Nome fantasia" htmlFor="trade_name" error={errors.trade_name?.message}>
          <Input id="trade_name" {...register('trade_name')} />
        </Field>
        <Field label="CNPJ" htmlFor="cnpj" error={errors.cnpj?.message} hint="Com ou sem pontuação.">
          <Input id="cnpj" {...register('cnpj')} placeholder="00.000.000/0000-00" />
        </Field>
        <div className="col-span-2">
          <Field label="Local / obra" htmlFor="location" error={errors.location?.message}
            hint="Onde as marmitas são entregues (ex.: Obra Av. Paulista, 1000).">
            <Input id="location" {...register('location')} />
          </Field>
        </div>
        <Field label="Nome do contato" htmlFor="contact_name" error={errors.contact_name?.message}>
          <Input id="contact_name" {...register('contact_name')} />
        </Field>
        <Field label="Telefone" htmlFor="phone" error={errors.phone?.message}>
          <Input id="phone" {...register('phone')} />
        </Field>
        <Field label="E-mail" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" {...register('email')} />
        </Field>
        <Field label="Ciclo de faturamento" htmlFor="billing_cycle" error={errors.billing_cycle?.message} required>
          <Select id="billing_cycle" {...register('billing_cycle')}>
            <option value="QUINZENAL">Quinzenal</option>
            <option value="MENSAL">Mensal</option>
          </Select>
        </Field>
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

export function CompaniesPage() {
  const [cycle, setCycle] = useState('')
  const r = useRegistry<Company>('companies', 'Empresa', { billing_cycle: cycle })
  const [editing, setEditing] = useState<Company | 'new' | null>(null)
  const data = r.list.data

  return (
    <>
      <PageHeader title="Empresas" subtitle="Empreiteiras — principais compradoras, faturamento quinzenal ou mensal."
        actions={<Button onClick={() => setEditing('new')}>Nova empresa</Button>} />
      <Card>
        <div className="mb-4 flex flex-wrap gap-3">
          <Input aria-label="Pesquisar" placeholder="Pesquisar por nome, CNPJ ou obra…" value={r.q}
            onChange={(e) => r.setQ(e.target.value)} className="w-80" />
          <Select aria-label="Situação" value={r.active} onChange={(e) => r.setActive(e.target.value as '' | 'true' | 'false')}>
            <option value="">Todas</option>
            <option value="true">Ativas</option>
            <option value="false">Inativas</option>
          </Select>
          <Select aria-label="Ciclo" value={cycle} onChange={(e) => { setCycle(e.target.value); r.setPage(1) }}>
            <option value="">Todos os ciclos</option>
            <option value="QUINZENAL">Quinzenal</option>
            <option value="MENSAL">Mensal</option>
          </Select>
        </div>
        {r.list.isLoading && <Loading />}
        {r.list.isError && <ErrorBox message={errorMessage(r.list.error)} />}
        {data && data.items.length === 0 && <EmptyState>Nenhuma empresa encontrada.</EmptyState>}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <thead><tr>
                <Th>Nome</Th><Th>Local / obra</Th><Th>CNPJ</Th><Th>Ciclo</Th><Th>Início</Th><Th>Pagamento</Th>
                <Th>Situação</Th><Th className="text-right">Ações</Th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <Td><div className="font-medium text-slate-900">{c.name}</div>
                      {c.trade_name && <div className="text-xs text-slate-500">{c.trade_name}</div>}</Td>
                    <Td>{c.location ?? '—'}</Td>
                    <Td className="tabular">{formatCnpj(c.cnpj)}</Td>
                    <Td>{BILLING_CYCLE_LABELS[c.billing_cycle]}</Td>
                    <Td className="tabular">{formatDate(c.start_date)}</Td>
                    <Td className="tabular">{formatDate(c.payment_date)}</Td>
                    <Td><ActiveBadge active={c.is_active} /></Td>
                    <Td className="whitespace-nowrap text-right">
                      <Link to={`/dashboard?empresa=${c.id}`} className="mr-2 text-sm text-brand-600 hover:underline">Dashboard</Link>
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
      {editing && <CompanyForm company={editing === 'new' ? undefined : editing} onClose={() => setEditing(null)} />}
    </>
  )
}
