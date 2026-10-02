import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { api, errorMessage } from '../../api/client'
import type { Page, User } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { useToast } from '../../components/Toast'
import { ActiveBadge, Button, Card, ErrorBox, Field, Input, Loading, Modal, PageHeader, Table, Td, Th } from '../../components/ui'
import { formatDate } from '../../lib/format'

function PasswordModal({ title, requireCurrent, onSubmit, onClose }: {
  title: string
  requireCurrent?: boolean
  onSubmit: (current: string, next: string) => Promise<void>
  onClose: () => void
}) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [error, setError] = useState<string | null>(null)
  async function submit(e: FormEvent) {
    e.preventDefault()
    if (next.length < 8) return setError('A nova senha deve ter pelo menos 8 caracteres.')
    try {
      await onSubmit(current, next)
      onClose()
    } catch (err) {
      setError(errorMessage(err))
    }
  }
  return (
    <Modal open title={title} onClose={onClose} footer={
      <><Button variant="secondary" onClick={onClose}>Cancelar</Button><Button type="submit" form="password-form">Salvar</Button></>
    }>
      <form id="password-form" onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {requireCurrent && (
          <Field label="Senha atual" htmlFor="current"><Input id="current" type="password" value={current}
            onChange={(e) => setCurrent(e.target.value)} /></Field>
        )}
        <Field label="Nova senha" htmlFor="next" hint="Mínimo de 8 caracteres."><Input id="next" type="password" value={next}
          onChange={(e) => setNext(e.target.value)} /></Field>
        {error && <ErrorBox message={error} />}
      </form>
    </Modal>
  )
}

function NewUserModal({ onClose }: { onClose: () => void }) {
  const notify = useToast()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState<string | null>(null)
  async function submit(e: FormEvent) {
    e.preventDefault()
    try {
      await api.post('/users', form)
      notify('Usuário cadastrado.')
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      onClose()
    } catch (err) {
      setError(errorMessage(err))
    }
  }
  return (
    <Modal open title="Novo usuário administrador" onClose={onClose} footer={
      <><Button variant="secondary" onClick={onClose}>Cancelar</Button><Button type="submit" form="user-form">Salvar</Button></>
    }>
      <form id="user-form" onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <Field label="Nome" htmlFor="u-name" required><Input id="u-name" value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
        <Field label="E-mail" htmlFor="u-email" required><Input id="u-email" type="email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
        <Field label="Senha" htmlFor="u-password" required hint="Mínimo de 8 caracteres."><Input id="u-password" type="password"
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
        {error && <ErrorBox message={error} />}
      </form>
    </Modal>
  )
}

export function UsersPage() {
  const { user: me } = useAuth()
  const notify = useToast()
  const queryClient = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [resetting, setResetting] = useState<User | null>(null)
  const [changingOwn, setChangingOwn] = useState(false)
  const users = useQuery({ queryKey: ['users'], queryFn: () => api.get<Page<User>>('/users', { page_size: 100 }) })
  const toggle = useMutation({
    mutationFn: (u: User) => api.post<User>(`/users/${u.id}/${u.is_active ? 'deactivate' : 'activate'}`),
    onSuccess: async () => { notify('Usuário atualizado.'); await queryClient.invalidateQueries({ queryKey: ['users'] }) },
    onError: (error) => notify(errorMessage(error), 'error'),
  })

  return (
    <>
      <PageHeader title="Usuários" subtitle="Todos os usuários são administradores (lançam vendas, custos e cadastros)."
        actions={<>
          <Button variant="secondary" onClick={() => setChangingOwn(true)}>Alterar minha senha</Button>
          <Button onClick={() => setCreating(true)}>Novo usuário</Button>
        </>} />
      <Card>
        {users.isLoading && <Loading />}
        {users.isError && <ErrorBox message={errorMessage(users.error)} />}
        {users.data && (
          <Table>
            <thead><tr><Th>Nome</Th><Th>E-mail</Th><Th>Último acesso</Th><Th>Situação</Th><Th className="text-right">Ações</Th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {users.data.items.map((u) => (
                <tr key={u.id}>
                  <Td className="font-medium text-slate-900">{u.name}{u.id === me?.id && <span className="ml-2 text-xs text-slate-500">(você)</span>}</Td>
                  <Td>{u.email}</Td>
                  <Td className="tabular">{u.last_login_at ? formatDate(u.last_login_at) : '—'}</Td>
                  <Td><ActiveBadge active={!!u.is_active} /></Td>
                  <Td className="whitespace-nowrap text-right">
                    <Button variant="ghost" onClick={() => setResetting(u)}>Redefinir senha</Button>
                    {u.id !== me?.id && (
                      <Button variant="ghost" onClick={() => toggle.mutate(u)}>{u.is_active ? 'Desativar' : 'Ativar'}</Button>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
      {creating && <NewUserModal onClose={() => setCreating(false)} />}
      {resetting && (
        <PasswordModal title={`Redefinir senha de ${resetting.name}`} onClose={() => setResetting(null)}
          onSubmit={async (_current, next) => {
            await api.post(`/users/${resetting.id}/reset-password`, { new_password: next })
            notify('Senha redefinida.')
          }} />
      )}
      {changingOwn && (
        <PasswordModal title="Alterar minha senha" requireCurrent onClose={() => setChangingOwn(false)}
          onSubmit={async (current, next) => {
            await api.post('/auth/change-password', { current_password: current, new_password: next })
            notify('Senha alterada.')
          }} />
      )}
    </>
  )
}
