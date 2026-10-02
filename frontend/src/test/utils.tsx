import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

import { setToken } from '../api/client'
import { AuthProvider } from '../auth/AuthContext'
import { ToastProvider } from '../components/Toast'

type Handler = (url: URL, init: RequestInit) => { status?: number; body?: unknown } | undefined

/** Simula a API: cada handler recebe a URL e devolve { status, body }. */
export function mockApi(handler: Handler) {
  const calls: { method: string; url: URL; body: unknown }[] = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input), 'http://localhost')
    const method = init.method ?? 'GET'
    calls.push({ method, url, body: init.body ? JSON.parse(String(init.body)) : undefined })
    const result = handler(url, { ...init, method }) ?? { status: 404, body: { error: { code: 'NOT_FOUND', message: 'x' } } }
    const status = result.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(result.body ?? {}), {
      status, headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return { calls, fetchMock }
}

export const ADMIN = { id: 1, name: 'Dono', email: 'dono@exemplo.com.br', role: 'ADMIN' }

export function renderApp(ui: ReactElement, { route = '/', loggedIn = true } = {}) {
  setToken(loggedIn ? 'token-de-teste' : null)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={[route]}>
          <AuthProvider>{ui}</AuthProvider>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

export function page<T>(items: T[]) {
  return { items, total: items.length, page: 1, page_size: 20, pages: items.length ? 1 : 0 }
}
