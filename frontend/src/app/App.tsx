import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ApiError } from '../api/client'
import { AuthProvider } from '../auth/AuthContext'
import { RequireAuth } from '../auth/RequireAuth'
import { ToastProvider } from '../components/Toast'
import { CategoriesPage } from '../features/categories/CategoriesPage'
import { CompaniesPage } from '../features/companies/CompaniesPage'
import { CostsPage } from '../features/costs/CostsPage'
import { CustomersPage } from '../features/customers/CustomersPage'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { HistoryPage } from '../features/history/HistoryPage'
import { SalesPage } from '../features/sales/SalesPage'
import { UsersPage } from '../features/users/UsersPage'
import { Layout } from './Layout'
import { LoginPage } from './LoginPage'

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
      },
    },
  })
}

const queryClient = createQueryClient()

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/lancamentos/vendas" element={<SalesPage />} />
        <Route path="/lancamentos/custos" element={<CostsPage />} />
        <Route path="/historico" element={<HistoryPage />} />
        <Route path="/cadastros/empresas" element={<CompaniesPage />} />
        <Route path="/cadastros/clientes" element={<CustomersPage />} />
        <Route path="/cadastros/categorias" element={<CategoriesPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}
