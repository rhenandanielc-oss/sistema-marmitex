/** Tipos das respostas da API (API.md). Dinheiro sempre como string decimal. */

export type Money = string
export type BuyerType = 'COMPANY' | 'CUSTOMER'
export type CostType = 'CUSTO_DIARIO' | 'CUSTO_FIXO'
export type PeriodPreset = 'today' | 'week' | 'month' | 'last_month' | 'custom'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Ref {
  id: number
  name: string
}

export interface User {
  id: number
  name: string
  email: string
  role: string
  is_active?: boolean
  last_login_at?: string | null
  version?: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_at: string
  user: User
}

export interface Company {
  id: number
  name: string
  trade_name: string | null
  cnpj: string | null
  contact_name: string | null
  phone: string | null
  email: string | null
  location: string | null
  billing_cycle: 'QUINZENAL' | 'MENSAL'
  start_date: string | null
  payment_date: string | null
  notes: string | null
  is_active: boolean
  version: number
}

export interface Customer {
  id: number
  name: string
  phone: string | null
  document: string | null
  location: string | null
  billing_cycle: 'A_VISTA' | 'SEMANAL' | 'QUINZENAL' | 'MENSAL'
  start_date: string | null
  payment_date: string | null
  notes: string | null
  is_active: boolean
  version: number
}

export interface Category {
  id: number
  name: string
  cost_type: CostType
  is_active: boolean
  version: number
}

export interface BuyerRef {
  type: BuyerType
  id: number
  name: string
}

export interface Sale {
  id: number
  sale_date: string
  buyer_type: BuyerType
  buyer: BuyerRef
  unit_price: Money
  quantity: number
  subtotal: Money
  notes: string | null
  version: number
  created_at: string
  created_by: Ref | null
}

export interface Cost {
  id: number
  cost_date: string
  category: Ref
  cost_type: CostType
  amount: Money
  description: string | null
  version: number
  created_at: string
  created_by: Ref | null
  running_total?: Money
}

export interface CostTotals {
  daily_costs: Money
  fixed_costs: Money
  total_costs: Money
  count: number
}

export interface CostPage extends Page<Cost> {
  totals: CostTotals
}

export interface PeriodInfo {
  preset: string
  start_date: string
  end_date: string
  days: number
}

export interface CostSummary extends CostTotals {
  period: PeriodInfo
}

export interface HistoryItem {
  kind: 'SALE' | 'COST'
  id: number
  date: string
  amount: Money
  sale: { buyer: BuyerRef; quantity: number; unit_price: Money; subtotal: Money } | null
  cost: { category: Ref; cost_type: CostType; amount: Money; description: string | null } | null
}

export interface HistoryPage extends Page<HistoryItem> {
  totals: {
    sales_total: Money
    sales_quantity: number
    sales_count: number
    costs_total: Money
    costs_count: number
  }
}

export interface Summary {
  period: PeriodInfo
  revenue: Money
  revenue_by_buyer_type: Record<BuyerType, Money>
  quantity: number
  quantity_by_buyer_type: Record<BuyerType, number>
  sales_count: number
  daily_costs: Money
  fixed_costs: Money
  total_costs: Money
  net_profit: Money
  net_margin_percent: Money | null
  average_cost_per_meal: Money | null
  average_ticket: Money | null
  average_price_per_meal: Money | null
}

export interface DailyItem {
  date: string
  revenue: Money
  quantity: number
  sales_count: number
  daily_costs: Money
  fixed_costs: Money
  total_costs: Money
  cumulative_costs: Money
  net_profit: Money
  cumulative_net_profit: Money
  average_cost_per_meal: Money | null
}

export interface Daily {
  period: PeriodInfo
  items: DailyItem[]
}

export interface BuyerRevenue {
  buyer: BuyerRef
  revenue: Money
  quantity: number
  sales_count: number
  average_ticket: Money | null
  average_price_per_meal: Money | null
  revenue_share_percent: Money | null
}

export interface ByBuyer {
  period: PeriodInfo
  revenue: Money
  items: BuyerRevenue[]
  subtotals: Record<BuyerType, { revenue: Money; quantity: number; sales_count: number }>
}

export interface SalesByCompanyDaily {
  period: PeriodInfo
  companies: Ref[]
  has_other_companies: boolean
  items: { date: string; values: Record<string, Money>; other_companies: Money; customers: Money }[]
}

export interface BuyerDashboard {
  period: PeriodInfo
  buyer: {
    type: BuyerType
    id: number
    name: string
    is_active: boolean
    billing_cycle: string
    start_date: string | null
    payment_date: string | null
  }
  revenue: Money
  quantity: number
  sales_count: number
  average_ticket: Money | null
  average_price_per_meal: Money | null
  revenue_share_percent: Money | null
  daily: { date: string; revenue: Money; quantity: number; sales_count: number }[]
  recent_sales: Sale[]
  comparison: {
    previous_period: PeriodInfo
    revenue: Money
    quantity: number
    sales_count: number
    revenue_change_percent: Money | null
  }
}
