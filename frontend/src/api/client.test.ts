import { describe, expect, it, vi } from 'vitest'

import { mockApi } from '../test/utils'
import { ApiError, api, buildQuery, getToken, setToken, UNAUTHORIZED_EVENT } from './client'

describe('cliente da API', () => {
  it('monta query string ignorando vazios', () => {
    expect(buildQuery({ a: 1, b: '', c: undefined, d: null, e: 'x y' })).toBe('?a=1&e=x+y')
    expect(buildQuery({})).toBe('')
  })

  it('envia o token e converte erros padronizados', async () => {
    setToken('abc')
    const { calls } = mockApi(() => ({
      status: 422,
      body: { error: { code: 'VALIDATION_ERROR', message: 'Dados inválidos.', details: [{ field: 'quantity', message: 'Deve ser maior que 0.' }] } },
    }))
    const error = await api.post('/sales', { quantity: 0 }).catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(422)
    expect(error.details[0].field).toBe('quantity')
    expect(calls[0].url.pathname).toBe('/api/v1/sales')
    expect((vi.mocked(fetch).mock.calls[0][1]?.headers as Record<string, string>).Authorization).toBe('Bearer abc')
  })

  it('401 encerra a sessão local', async () => {
    setToken('expirado')
    mockApi(() => ({ status: 401, body: { error: { code: 'UNAUTHENTICATED', message: 'Sessão expirada.' } } }))
    const listener = vi.fn()
    window.addEventListener(UNAUTHORIZED_EVENT, listener)
    await api.get('/auth/me').catch(() => undefined)
    expect(getToken()).toBeNull()
    expect(listener).toHaveBeenCalled()
    window.removeEventListener(UNAUTHORIZED_EVENT, listener)
  })

  it('erro de rede vira mensagem amigável', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('fail') }))
    const error = await api.get('/x').catch((e) => e)
    expect(error.code).toBe('NETWORK_ERROR')
  })
})
