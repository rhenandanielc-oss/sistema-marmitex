import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ADMIN, mockApi, renderApp } from '../test/utils'
import { AppRoutes } from './App'

describe('rotas protegidas (FE-01)', () => {
  it('sem sessão redireciona para o login', async () => {
    mockApi(() => undefined)
    renderApp(<AppRoutes />, { route: '/lancamentos/vendas', loggedIn: false })
    expect(await screen.findByRole('button', { name: 'Entrar' })).toBeInTheDocument()
  })

  it('login mostra erro da API e depois entra', async () => {
    let attempts = 0
    mockApi((url) => {
      if (url.pathname === '/api/v1/auth/login') {
        attempts += 1
        return attempts === 1
          ? { status: 401, body: { error: { code: 'INVALID_CREDENTIALS', message: 'E-mail ou senha inválidos.' } } }
          : { body: { access_token: 't', token_type: 'bearer', expires_at: '2026-10-02T20:00:00Z', user: ADMIN } }
      }
      return { body: { items: [], total: 0, page: 1, page_size: 20, pages: 0 } }
    })
    renderApp(<AppRoutes />, { route: '/cadastros/empresas', loggedIn: false })
    await userEvent.type(await screen.findByLabelText('E-mail'), 'dono@exemplo.com.br')
    await userEvent.type(screen.getByLabelText('Senha'), 'errada')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha inválidos.')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('heading', { name: 'Empresas' })).toBeInTheDocument()
    expect(screen.getByText('Dono')).toBeInTheDocument()
  })
})
