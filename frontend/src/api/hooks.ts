import { useQuery } from '@tanstack/react-query'

import { api } from './client'
import type { Category, Company, Customer, Page } from './types'

/** Listas para seleção em lançamentos e filtros. `onlyActive` = somente ativos (novos lançamentos). */
export function useCompanyOptions(onlyActive: boolean) {
  return useQuery({
    queryKey: ['companies', 'options', onlyActive],
    queryFn: () => api.get<Page<Company>>('/companies', { page_size: 100, active: onlyActive ? true : undefined }),
  })
}

export function useCustomerOptions(onlyActive: boolean) {
  return useQuery({
    queryKey: ['customers', 'options', onlyActive],
    queryFn: () => api.get<Page<Customer>>('/customers', { page_size: 100, active: onlyActive ? true : undefined }),
  })
}

export function useCategoryOptions(onlyActive: boolean) {
  return useQuery({
    queryKey: ['cost-categories', 'options', onlyActive],
    queryFn: () => api.get<Page<Category>>('/cost-categories', {
      page_size: 100, active: onlyActive ? true : undefined, sort: 'name',
    }),
  })
}

/** Chaves invalidadas após qualquer lançamento (ARCHITECTURE.md seção 6). */
export const ENTRY_KEYS = [['sales'], ['costs'], ['history'], ['dashboard']] as const
