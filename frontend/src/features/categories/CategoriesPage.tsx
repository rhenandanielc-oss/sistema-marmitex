import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError, errorMessage } from '../../api/client'
import type { Category } from '../../api/types'
import { useToast } from '../../components/Toast'
import { ActiveBadge, Badge, Button, Card, EmptyState, ErrorBox, Field, Input, Loading, Modal, PageHeader,
  Pagination, Select, Table, Td, Th } from '../../components/ui'
import { applyServerErrors } from '../../lib/forms'
import { COST_TYPE_LABELS } from '../../lib/format'
import { useRegistry, useSaveRegistry } from '../registry'

const schema = z.object({
  name: z.string().trim().min(2, 'Informe o nome (mínimo 2 caracteres).').max(80),
  cost_type: z.enum(['CUSTO_DIARIO', 'CUSTO_FIXO']),
})
type FormValues = z.infer<typeof schema>

function CategoryForm({ category, onClose }: { category?: Category; onClose: () => void }) {
  const notify = useToast()
  const save = useSaveRegistry<Category>('cost-categories')
  const [formError, setFormError] = useState<string | null>(null)
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: category?.name ?? '', cost_type: category?.cost_type ?? 'CUSTO_DIARIO' },
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const body: Record<string, unknown> = { ...values }
    if (category) body.version = category.version
    try {
      await save.mutateAsync({ id: category?.id, body })
      notify(category ? 'Tipo de custo atualizado.' : 'Tipo de custo cadastrado.')
      onClose()
    } catch (error) {
      if (!applyServerErrors(error, setError, ['name', 'cost_type'])) setFormError(errorMessage(error))
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') onClose()
    }
  }

  return (
    <Modal open title={category ? 'Editar tipo de custo' : 'Novo tipo de custo'} onClose={onClose} footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button type="submit" form="category-form" disabled={isSubmitting}>Salvar</Button>
      </>
    }>
      <form id="category-form" onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
        <Field label="Nome" htmlFor="name" error={errors.name?.message} required hint="Ex.: Embalagens, Ingredientes.">
          <Input id="name" {...register('name')} autoFocus />
        </Field>
        <Field label="Classificação" htmlFor="cost_type" error={errors.cost_type?.message} required
          hint="Diário: gastos do dia a dia. Fixo: despesas mensais (aluguel, salários…).">
          <Select id="cost_type" {...register('cost_type')}>
            <option value="CUSTO_DIARIO">Custo diário</option>
            <option value="CUSTO_FIXO">Custo fixo</option>
          </Select>
        </Field>
        {formError && <ErrorBox message={formError} />}
      </form>
    </Modal>
  )
}

export function CategoriesPage() {
  const [costType, setCostType] = useState('')
  const r = useRegistry<Category>('cost-categories', 'Tipo de custo', { cost_type: costType })
  const [editing, setEditing] = useState<Category | 'new' | null>(null)
  const data = r.list.data

  return (
    <>
      <PageHeader title="Tipos de custo" subtitle="Categorias usadas no lançamento dos custos do restaurante."
        actions={<Button onClick={() => setEditing('new')}>Novo tipo de custo</Button>} />
      <Card>
        <div className="mb-4 flex flex-wrap gap-3">
          <Input aria-label="Pesquisar" placeholder="Pesquisar…" value={r.q} onChange={(e) => r.setQ(e.target.value)} className="w-64" />
          <Select aria-label="Classificação" value={costType} onChange={(e) => { setCostType(e.target.value); r.setPage(1) }}>
            <option value="">Diários e fixos</option>
            <option value="CUSTO_DIARIO">Diários</option>
            <option value="CUSTO_FIXO">Fixos</option>
          </Select>
          <Select aria-label="Situação" value={r.active} onChange={(e) => r.setActive(e.target.value as '' | 'true' | 'false')}>
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </Select>
        </div>
        {r.list.isLoading && <Loading />}
        {r.list.isError && <ErrorBox message={errorMessage(r.list.error)} />}
        {data && data.items.length === 0 && <EmptyState>Nenhum tipo de custo encontrado.</EmptyState>}
        {data && data.items.length > 0 && (
          <>
            <Table>
              <thead><tr><Th>Nome</Th><Th>Classificação</Th><Th>Situação</Th><Th className="text-right">Ações</Th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((c) => (
                  <tr key={c.id}>
                    <Td className="font-medium text-slate-900">{c.name}</Td>
                    <Td><Badge tone={c.cost_type === 'CUSTO_FIXO' ? 'amber' : 'blue'}>{COST_TYPE_LABELS[c.cost_type]}</Badge></Td>
                    <Td><ActiveBadge active={c.is_active} /></Td>
                    <Td className="whitespace-nowrap text-right">
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
      {editing && <CategoryForm category={editing === 'new' ? undefined : editing} onClose={() => setEditing(null)} />}
    </>
  )
}
