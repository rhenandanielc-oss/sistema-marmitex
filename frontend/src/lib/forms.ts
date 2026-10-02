import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'

import { ApiError } from '../api/client'

/**
 * Aplica erros de campo vindos da API (error.details) ao formulário.
 * Retorna true se algum erro foi associado a um campo do formulário.
 */
export function applyServerErrors<T extends FieldValues>(error: unknown, setError: UseFormSetError<T>,
  fields: readonly string[]): boolean {
  if (!(error instanceof ApiError)) return false
  let applied = false
  for (const detail of error.details) {
    if (fields.includes(detail.field)) {
      setError(detail.field as Path<T>, { type: 'server', message: detail.message })
      applied = true
    }
  }
  return applied
}

/** Converte "" em null para campos opcionais antes de enviar à API. */
export function blankToNull<T extends Record<string, unknown>>(values: T): T {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(values)) out[k] = typeof v === 'string' && v.trim() === '' ? null : v
  return out as T
}
