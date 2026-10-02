import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { errorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Button, ErrorBox, Field, Input } from '../components/ui'

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  if (user) return <Navigate to={from} replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-lg bg-white p-6 shadow-md" noValidate>
        <h1 className="text-lg font-semibold text-slate-900">Marmitex B2B</h1>
        <p className="mb-5 text-sm text-slate-500">Entre com seu e-mail e senha.</p>
        <div className="flex flex-col gap-4">
          <Field label="E-mail" htmlFor="email">
            <Input id="email" type="email" autoComplete="username" value={email} required
              onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Senha" htmlFor="password">
            <Input id="password" type="password" autoComplete="current-password" value={password} required
              onChange={(e) => setPassword(e.target.value)} />
          </Field>
          {error && <ErrorBox message={error} />}
          <Button type="submit" disabled={busy || !email || !password}>{busy ? 'Entrando…' : 'Entrar'}</Button>
        </div>
      </form>
    </div>
  )
}
