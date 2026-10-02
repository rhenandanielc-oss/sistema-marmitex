"""Schemas de histórico e dashboard (API.md seções 3.9 e 3.10)."""

from datetime import date
from typing import Literal

from app.schemas.common import MoneyOut, OptionalMoneyOut, OutputModel, Ref
from app.schemas.entries import BuyerRef, PeriodOut, SaleRead

# ---------- Histórico ----------

class HistorySale(OutputModel):
    buyer: BuyerRef
    quantity: int
    unit_price: MoneyOut
    subtotal: MoneyOut


class HistoryCost(OutputModel):
    category: Ref
    cost_type: str
    amount: MoneyOut
    description: str | None


class HistoryItem(OutputModel):
    kind: Literal["SALE", "COST"]
    id: int
    date: date
    amount: MoneyOut
    sale: HistorySale | None
    cost: HistoryCost | None


class HistoryTotals(OutputModel):
    sales_total: MoneyOut
    sales_quantity: int
    sales_count: int
    costs_total: MoneyOut
    costs_count: int


class HistoryPage(OutputModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
    pages: int
    totals: HistoryTotals


# ---------- Dashboard ----------

class SummaryOut(OutputModel):
    period: PeriodOut
    revenue: MoneyOut
    revenue_by_buyer_type: dict[str, MoneyOut]
    quantity: int
    quantity_by_buyer_type: dict[str, int]
    sales_count: int
    daily_costs: MoneyOut
    fixed_costs: MoneyOut
    total_costs: MoneyOut
    net_profit: MoneyOut
    net_margin_percent: OptionalMoneyOut
    average_cost_per_meal: OptionalMoneyOut
    average_ticket: OptionalMoneyOut
    average_price_per_meal: OptionalMoneyOut


class DailyItem(OutputModel):
    date: date
    revenue: MoneyOut
    quantity: int
    sales_count: int
    daily_costs: MoneyOut
    fixed_costs: MoneyOut
    total_costs: MoneyOut
    cumulative_costs: MoneyOut
    net_profit: MoneyOut
    cumulative_net_profit: MoneyOut
    average_cost_per_meal: OptionalMoneyOut


class DailyOut(OutputModel):
    period: PeriodOut
    items: list[DailyItem]


class BuyerRevenueItem(OutputModel):
    buyer: BuyerRef
    revenue: MoneyOut
    quantity: int
    sales_count: int
    average_ticket: OptionalMoneyOut
    average_price_per_meal: OptionalMoneyOut
    revenue_share_percent: OptionalMoneyOut


class Subtotal(OutputModel):
    revenue: MoneyOut
    quantity: int
    sales_count: int


class ByBuyerOut(OutputModel):
    period: PeriodOut
    revenue: MoneyOut
    items: list[BuyerRevenueItem]
    subtotals: dict[str, Subtotal]


class CompanySeriesItem(OutputModel):
    date: date
    values: dict[str, MoneyOut]
    other_companies: MoneyOut
    customers: MoneyOut


class SalesByCompanyDailyOut(OutputModel):
    period: PeriodOut
    companies: list[Ref]
    has_other_companies: bool
    items: list[CompanySeriesItem]


class BuyerInfo(OutputModel):
    type: str
    id: int
    name: str
    is_active: bool
    billing_cycle: str
    start_date: date | None
    payment_date: date | None


class BuyerDailyItem(OutputModel):
    date: date
    revenue: MoneyOut
    quantity: int
    sales_count: int


class ComparisonOut(OutputModel):
    previous_period: PeriodOut
    revenue: MoneyOut
    quantity: int
    sales_count: int
    revenue_change_percent: OptionalMoneyOut


class BuyerDashboardOut(OutputModel):
    period: PeriodOut
    buyer: BuyerInfo
    revenue: MoneyOut
    quantity: int
    sales_count: int
    average_ticket: OptionalMoneyOut
    average_price_per_meal: OptionalMoneyOut
    revenue_share_percent: OptionalMoneyOut
    daily: list[BuyerDailyItem]
    recent_sales: list[SaleRead]
    comparison: ComparisonOut
