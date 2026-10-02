import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ADMIN, mockApi, page, renderApp } from '../test/utils'
import { CostsPage } from './costs/CostsPage'
import { DashboardPage } from './dashboard/DashboardPage'
import { SalesPage } from './sales/SalesPage'

const nbsp = (s: string | null) => (s ?? '').replace(/\u00a0/g, ' ')
const COMPANY = { id: 7, name: 'Construtora Alfa', location: 'Obra Centro', is_active: true, version: 1, default_delivery_type: 'OBRA' }
const INACTIVE = { id: 8, name: 'Empresa Antiga', location: null, is_active: false, version: 1, default_delivery_type: 'OBRA' }
const CUSTOMER = { id: 3, name: 'João da Obra', location: null, is_active: true, version: 1, default_delivery_type: 'ENTREGA' }
const TOTALS = { sales_total: '0.00', sales_quantity: 0, sales_count: 0, sales_pending_total: '0.00', costs_total: '0.00', costs_count: 0 }

describe('Vendas (FE-02, FE-03, FE-04)', () => {
  function setup(saleResponse: { status?: number; body: unknown }) {
    return mockApi((url, init) => {
      const p = url.pathname
      if (p === '/api/v1/auth/me') return { body: ADMIN }
      if (p === '/api/v1/companies') return { body: page([COMPANY, INACTIVE]) }
      if (p === '/api/v1/customers') return { body: page([CUSTOMER]) }
      if (p === '/api/v1/history') return { body: { ...page([]), totals: TOTALS } }
      if (p === '/api/v1/sales' && init.method === 'POST') return saleResponse
      if (p === '/api/v1/sales') return { body: page([]) }
      return undefined
    })
  }

  it('lista só compradores ativos e troca entre empresa e cliente', async () => {
    setup({ body: {} })
    renderApp(<SalesPage />)
    const select = await screen.findByLabelText(/^Empresa/, { selector: 'select' })
    await waitFor(() => expect(within(select).getByText(/Construtora Alfa/)).toBeInTheDocument())
    expect(within(select).queryByText(/Empresa Antiga/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByLabelText('Cliente avulso'))
    const customerSelect = await screen.findByLabelText(/^Cliente/, { selector: 'select' })
    expect(within(customerSelect).getByText('João da Obra')).toBeInTheDocument()
  })

  it('envia a venda com data escolhida e mostra o subtotal calculado pelo servidor', async () => {
    const { calls } = setup({
      status: 201,
      body: { id: 1, buyer: { type: 'COMPANY', id: 7, name: 'Construtora Alfa' }, quantity: 40, subtotal: '740.00' },
    })
    renderApp(<SalesPage />)
    const select = await screen.findByLabelText(/^Empresa/, { selector: 'select' })
    await waitFor(() => expect(within(select).getByText(/Construtora Alfa/)).toBeInTheDocument())
    await userEvent.selectOptions(select, '7')
    await userEvent.clear(screen.getByLabelText(/Preço unitário/))
    await userEvent.type(screen.getByLabelText(/Preço unitário/), '18,50')
    await userEvent.type(screen.getByLabelText(/Quantidade/), '40')
    const date = screen.getByLabelText(/^Data/)
    await userEvent.clear(date)
    await userEvent.type(date, '2026-09-29')
    await userEvent.click(screen.getByRole('button', { name: 'Registrar venda' }))
    expect(nbsp((await screen.findByRole('status')).textContent)).toContain('R$ 740,00')
    const post = calls.find((c) => c.method === 'POST')!
    expect(post.body).toEqual({ buyer_type: 'COMPANY', company_id: 7, customer_id: null, unit_price: '18.50',
      quantity: 40, sale_date: '2026-09-29', delivery_type: 'OBRA', payment_status: 'PENDENTE', notes: null })
  })

  it('recebimento vem do cadastro do cliente e o pagamento pode ser marcado', async () => {
    const { calls } = setup({
      status: 201,
      body: { id: 2, buyer: { type: 'CUSTOMER', id: 3, name: 'João da Obra' }, quantity: 1, subtotal: '22.00' },
    })
    renderApp(<SalesPage />)
    await screen.findByLabelText(/^Empresa/, { selector: 'select' })
    await userEvent.click(screen.getByLabelText('Cliente avulso'))
    const select = await screen.findByLabelText(/^Cliente/, { selector: 'select' })
    await waitFor(() => expect(within(select).getByText('João da Obra')).toBeInTheDocument())
    await userEvent.selectOptions(select, '3')
    await waitFor(() => expect(screen.getByLabelText(/^Recebimento/, { selector: 'select#new-delivery' })).toHaveValue('ENTREGA'))
    await userEvent.type(screen.getByLabelText(/Preço unitário/), '22')
    await userEvent.type(screen.getByLabelText(/Quantidade/), '1')
    await userEvent.click(screen.getByLabelText('Pago'))
    await userEvent.click(screen.getByRole('button', { name: 'Registrar venda' }))
    await screen.findByRole('status')
    const post = calls.find((c) => c.method === 'POST')!.body as Record<string, unknown>
    expect(post).toMatchObject({ buyer_type: 'CUSTOMER', customer_id: 3, delivery_type: 'ENTREGA', payment_status: 'PAGO' })
  })

  it('exibe erro de campo vindo da API', async () => {
    setup({ status: 422, body: { error: { code: 'VALIDATION_ERROR', message: 'Dados inválidos.',
      details: [{ field: 'sale_date', message: 'A data não pode ser futura.' }] } } })
    renderApp(<SalesPage />)
    const select = await screen.findByLabelText(/^Empresa/, { selector: 'select' })
    await waitFor(() => expect(within(select).getByText(/Construtora Alfa/)).toBeInTheDocument())
    await userEvent.selectOptions(select, '7')
    await userEvent.type(screen.getByLabelText(/Preço unitário/), '10')
    await userEvent.type(screen.getByLabelText(/Quantidade/), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Registrar venda' }))
    expect(await screen.findByText('A data não pode ser futura.')).toBeInTheDocument()
  })

  it('valida campos antes de enviar', async () => {
    const { calls } = setup({ body: {} })
    renderApp(<SalesPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Registrar venda' }))
    expect(await screen.findByText('Selecione o comprador.')).toBeInTheDocument()
    expect(calls.some((c) => c.method === 'POST')).toBe(false)
  })
})

describe('Custos (FE-09)', () => {
  it('mostra totais do mês e a coluna Acumulado vindos da API', async () => {
    mockApi((url) => {
      const p = url.pathname
      if (p === '/api/v1/auth/me') return { body: ADMIN }
      if (p === '/api/v1/cost-categories') return { body: page([{ id: 1, name: 'Ingredientes', cost_type: 'CUSTO_DIARIO', is_active: true, version: 1 }]) }
      if (p === '/api/v1/costs/summary') return { body: { daily_costs: '433.33', fixed_costs: '300.00', total_costs: '733.33', count: 3,
        period: { preset: 'month', start_date: '2026-09-01', end_date: '2026-09-30', days: 30 } } }
      if (p === '/api/v1/costs') return { body: { ...page([
        { id: 2, cost_date: '2026-09-05', category: { id: 7, name: 'Aluguel' }, cost_type: 'CUSTO_FIXO', amount: '300.00',
          running_total: '700.00', description: null, version: 1, created_at: '', created_by: null },
      ]), totals: { daily_costs: '433.33', fixed_costs: '300.00', total_costs: '733.33', count: 3 } } }
      return undefined
    })
    renderApp(<CostsPage />)
    const label = await screen.findByText('Custos totais no mês')
    await waitFor(() => expect(nbsp(label.parentElement!.textContent)).toContain('R$ 733,33'))
    const row = (await screen.findByText('Aluguel')).closest('tr')!
    expect(nbsp(row.textContent)).toContain('R$ 300,00')
    expect(nbsp(row.textContent)).toContain('R$ 700,00')
  })
})

describe('Dashboard (FE-06, FE-07)', () => {
  it('exibe exatamente os valores calculados pelo backend', async () => {
    const period = { preset: 'month', start_date: '2026-09-01', end_date: '2026-09-30', days: 30 }
    const { calls } = mockApi((url) => {
      const p = url.pathname
      if (p === '/api/v1/auth/me') return { body: ADMIN }
      if (p === '/api/v1/dashboard/summary') return { body: {
        period, revenue: '1535.00', revenue_by_buyer_type: { COMPANY: '1425.00', CUSTOMER: '110.00' }, quantity: 80,
        quantity_by_buyer_type: { COMPANY: 75, CUSTOMER: 5 }, sales_count: 4, daily_costs: '433.33', fixed_costs: '300.00',
        total_costs: '733.33', net_profit: '801.67', net_margin_percent: '52.23', average_cost_per_meal: '9.17',
        average_ticket: '383.75', average_price_per_meal: '19.19', pending_revenue: '400.00' } }
      if (p === '/api/v1/dashboard/daily') return { body: { period, items: [] } }
      if (p === '/api/v1/dashboard/by-buyer') return { body: { period, revenue: '1535.00', items: [
        { buyer: { type: 'COMPANY', id: 1, name: 'Empresa A' }, revenue: '925.00', quantity: 50, sales_count: 2,
          average_ticket: '462.50', average_price_per_meal: '18.50', revenue_share_percent: '60.26', pending_revenue: '100.00' }],
        subtotals: { COMPANY: { revenue: '1425.00', quantity: 75, sales_count: 3 }, CUSTOMER: { revenue: '110.00', quantity: 5, sales_count: 1 } } } }
      if (p === '/api/v1/dashboard/sales-by-company-daily') return { body: { period, companies: [], has_other_companies: false, items: [] } }
      if (p === '/api/v1/companies' || p === '/api/v1/customers') return { body: page([]) }
      return undefined
    })
    renderApp(<DashboardPage />, { route: '/dashboard' })
    const profit = await screen.findByText('Lucro líquido')
    expect(nbsp(profit.parentElement!.textContent)).toContain('R$ 801,67')
    expect(nbsp(profit.parentElement!.textContent)).toContain('Margem 52,23%')
    expect(nbsp(screen.getByText('Custo médio por marmita').parentElement!.textContent)).toContain('R$ 9,17')
    expect(await screen.findByText('60,26%')).toBeInTheDocument()
    expect(screen.getByText('Período: 01/09/2026 a 30/09/2026 (30 dia(s))')).toBeInTheDocument()
    expect(calls.find((c) => c.url.pathname === '/api/v1/dashboard/summary')!.url.searchParams.get('period')).toBe('month')

    await userEvent.click(screen.getByRole('button', { name: 'Mês anterior' }))
    await waitFor(() => expect(calls.some((c) => c.url.searchParams.get('period') === 'last_month')).toBe(true))
  })
})
