import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { ApiError, api, errorMessage, type QueryParams } from '../api/client'
import type { Page } from '../api/types'
import { useToast } from '../components/Toast'

/** Estado e consultas comuns às telas de cadastro (lista paginada + ativar/desativar). */
export function useRegistry<T extends { id: number; version: number; is_active: boolean }>(
  resource: string, label: string, extraParams: QueryParams = {},
) {
  const [q, setQ] = useState('')
  const [active, setActive] = useState<'true' | 'false' | ''>('')
  const [page, setPage] = useState(1)
  const queryClient = useQueryClient()
  const notify = useToast()
  const params: QueryParams = { q, active, page, page_size: 20, ...extraParams }

  const list = useQuery({
    queryKey: [resource, 'list', params],
    queryFn: () => api.get<Page<T>>(`/${resource}`, params),
    placeholderData: (previous) => previous,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [resource] })

  const toggle = useMutation({
    mutationFn: (item: T) =>
      api.post<T>(`/${resource}/${item.id}/${item.is_active ? 'deactivate' : 'activate'}`, { version: item.version }),
    onSuccess: (item) => {
      notify(`${label} ${item.is_active ? 'ativado(a)' : 'desativado(a)'}.`)
      void invalidate()
    },
    onError: (error) => {
      notify(errorMessage(error), 'error')
      if (error instanceof ApiError && error.code === 'VERSION_CONFLICT') void invalidate()
    },
  })

  return {
    q, setQ: (v: string) => { setQ(v); setPage(1) },
    active, setActive: (v: 'true' | 'false' | '') => { setActive(v); setPage(1) },
    page, setPage, list, toggle, invalidate,
  }
}

/** Salva (cria ou edita) um cadastro. */
export function useSaveRegistry<T>(resource: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id?: number; body: Record<string, unknown> }) =>
      id ? api.patch<T>(`/${resource}/${id}`, body) : api.post<T>(`/${resource}`, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [resource] }),
  })
}
