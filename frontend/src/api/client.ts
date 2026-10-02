/** Cliente HTTP da API (API.md). Envia o token e traduz erros padronizados. */

export interface FieldErrorDetail {
  field: string
  message: string
}

export class ApiError extends Error {
  status: number
  code: string
  details: FieldErrorDetail[]

  constructor(status: number, code: string, message: string, details: FieldErrorDetail[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const TOKEN_KEY = 'marmitex.token'

let token: string | null = readToken()

function readToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function getToken(): string | null {
  return token
}

export function setToken(value: string | null): void {
  token = value
  try {
    if (value) sessionStorage.setItem(TOKEN_KEY, value)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* armazenamento indisponível: mantém só em memória */
  }
}

export const UNAUTHORIZED_EVENT = 'marmitex:unauthorized'

export type QueryParams = Record<string, string | number | boolean | null | undefined>

export function buildQuery(params?: QueryParams): string {
  if (!params) return ''
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    search.set(key, String(value))
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  params?: QueryParams
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}${buildQuery(options.params)}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Não foi possível conectar ao servidor. Verifique se o sistema está ligado.')
  }

  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const err = data?.error
    const apiError = new ApiError(
      response.status,
      err?.code ?? 'ERROR',
      err?.message ?? 'Erro inesperado.',
      Array.isArray(err?.details) ? err.details : [],
    )
    if (response.status === 401 && !path.startsWith('/auth/login')) {
      setToken(null)
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    }
    throw apiError
  }
  return data as T
}

export const api = {
  get: <T>(path: string, params?: QueryParams) => apiRequest<T>(path, { params }),
  post: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: 'POST', body: body ?? {} }),
  patch: <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'PATCH', body }),
  delete: (path: string) => apiRequest<void>(path, { method: 'DELETE' }),
}

/** Mensagem amigável para qualquer erro. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.details.length === 1 && error.code === 'VALIDATION_ERROR') return error.details[0].message
    return error.message
  }
  return 'Erro inesperado.'
}
