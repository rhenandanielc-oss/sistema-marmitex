"""Motor financeiro — funções puras (FINANCIAL-RULES.md).

Sem acesso a banco, relógio ou HTTP. Recebe agregados (somas já feitas no PostgreSQL) e aplica as fórmulas
oficiais. Toda divisão passa por `_divide`, que nunca divide por zero (R-IND-2) e arredonda somente o resultado
final com ROUND_HALF_UP (seção 1 / R-IND-3).
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
HUNDRED = Decimal(100)

MAX_UNIT_PRICE = Decimal("9999.99")
MAX_QUANTITY = 10000
MAX_COST_AMOUNT = Decimal("9999999.99")

BUYER_COMPANY = "COMPANY"
BUYER_CUSTOMER = "CUSTOMER"
BUYER_TYPES = (BUYER_COMPANY, BUYER_CUSTOMER)


def round_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _divide(numerator: Decimal, denominator: Decimal | int, scale: Decimal = Decimal(1)) -> Decimal | None:
    if denominator == 0:
        return None
    return round_money(numerator * scale / Decimal(denominator))


def sale_subtotal(unit_price: Decimal, quantity: int) -> Decimal:
    """R-VEN-1: SUBTOTAL = PRECO_UNITARIO × QUANTIDADE (exato, sem arredondamento)."""
    if unit_price <= 0 or quantity <= 0:
        raise ValueError("Preço unitário e quantidade devem ser positivos.")
    if unit_price != unit_price.quantize(CENT):
        raise ValueError("Preço unitário deve ter no máximo 2 casas decimais.")
    return (unit_price * quantity).quantize(CENT)


def percent_change(current: Decimal, previous: Decimal) -> Decimal | None:
    """F-18: variação percentual; None se o valor anterior for zero."""
    return _divide(current - previous, previous, HUNDRED)


def running_totals(amounts: Iterable[Decimal]) -> list[Decimal]:
    """R-CUS-7: acumulado lançamento a lançamento, na ordem recebida (cronológica)."""
    total = ZERO
    result = []
    for amount in amounts:
        total += amount
        result.append(total)
    return result


@dataclass(frozen=True)
class SalesTotals:
    revenue: Decimal = ZERO
    quantity: int = 0
    sales_count: int = 0

    def __add__(self, other: "SalesTotals") -> "SalesTotals":
        return SalesTotals(self.revenue + other.revenue, self.quantity + other.quantity,
                           self.sales_count + other.sales_count)


@dataclass(frozen=True)
class CostTotals:
    daily: Decimal = ZERO
    fixed: Decimal = ZERO
    count: int = 0

    @property
    def total(self) -> Decimal:
        """F-05: CT = CF + CD."""
        return self.fixed + self.daily

    def __add__(self, other: "CostTotals") -> "CostTotals":
        return CostTotals(self.daily + other.daily, self.fixed + other.fixed, self.count + other.count)


@dataclass(frozen=True)
class FinancialSummary:
    revenue: Decimal
    revenue_by_buyer_type: dict[str, Decimal]
    quantity: int
    quantity_by_buyer_type: dict[str, int]
    sales_count: int
    daily_costs: Decimal
    fixed_costs: Decimal
    total_costs: Decimal
    net_profit: Decimal
    net_margin_percent: Decimal | None
    average_cost_per_meal: Decimal | None
    average_ticket: Decimal | None
    average_price_per_meal: Decimal | None


def summarize(sales_by_type: dict[str, SalesTotals], costs: CostTotals) -> FinancialSummary:
    """Indicadores gerais F-01 a F-11 (empresas + clientes avulsos + todos os custos)."""
    by_type = {t: sales_by_type.get(t, SalesTotals()) for t in BUYER_TYPES}
    sales = sum(by_type.values(), SalesTotals())
    total_costs = costs.total
    net_profit = sales.revenue - total_costs  # F-06
    return FinancialSummary(
        revenue=sales.revenue,
        revenue_by_buyer_type={t: v.revenue for t, v in by_type.items()},
        quantity=sales.quantity,
        quantity_by_buyer_type={t: v.quantity for t, v in by_type.items()},
        sales_count=sales.sales_count,
        daily_costs=costs.daily,
        fixed_costs=costs.fixed,
        total_costs=total_costs,
        net_profit=net_profit,
        net_margin_percent=_divide(net_profit, sales.revenue, HUNDRED),  # F-11
        average_cost_per_meal=_divide(total_costs, sales.quantity),  # F-07
        average_ticket=_divide(sales.revenue, sales.sales_count),  # F-09
        average_price_per_meal=_divide(sales.revenue, sales.quantity),  # F-10
    )


@dataclass(frozen=True)
class DayResult:
    date: date
    revenue: Decimal
    cumulative_revenue: Decimal
    quantity: int
    sales_count: int
    daily_costs: Decimal
    fixed_costs: Decimal
    total_costs: Decimal
    cumulative_costs: Decimal
    net_profit: Decimal
    cumulative_net_profit: Decimal
    average_cost_per_meal: Decimal | None


def daily_series(days: Sequence[date], sales: dict[date, SalesTotals],
                 costs: dict[date, CostTotals]) -> list[DayResult]:
    """R-IND-4: fórmulas aplicadas a cada dia; dias sem movimento = 0. Inclui acumulados (R-CUS-7)."""
    result = []
    cumulative_revenue = ZERO
    cumulative_costs = ZERO
    cumulative_profit = ZERO
    for day in days:
        s = sales.get(day, SalesTotals())
        c = costs.get(day, CostTotals())
        profit = s.revenue - c.total
        cumulative_revenue += s.revenue
        cumulative_costs += c.total
        cumulative_profit += profit
        result.append(DayResult(
            date=day, revenue=s.revenue, cumulative_revenue=cumulative_revenue, quantity=s.quantity,
            sales_count=s.sales_count,
            daily_costs=c.daily, fixed_costs=c.fixed, total_costs=c.total, cumulative_costs=cumulative_costs,
            net_profit=profit, cumulative_net_profit=cumulative_profit,
            average_cost_per_meal=_divide(c.total, s.quantity),
        ))
    return result


@dataclass(frozen=True)
class BuyerTotals:
    buyer_type: str
    buyer_id: int
    name: str
    totals: SalesTotals


@dataclass(frozen=True)
class BuyerRevenue:
    """Faturamento de um comprador (F-12 a F-17). Sem custos nem lucro (R-FAT-1)."""

    buyer_type: str
    buyer_id: int
    name: str
    revenue: Decimal
    quantity: int
    sales_count: int
    average_ticket: Decimal | None
    average_price_per_meal: Decimal | None
    revenue_share_percent: Decimal | None


def buyer_revenue(buyer: BuyerTotals, total_revenue: Decimal) -> BuyerRevenue:
    t = buyer.totals
    return BuyerRevenue(
        buyer_type=buyer.buyer_type, buyer_id=buyer.buyer_id, name=buyer.name,
        revenue=t.revenue, quantity=t.quantity, sales_count=t.sales_count,
        average_ticket=_divide(t.revenue, t.sales_count),  # F-15
        average_price_per_meal=_divide(t.revenue, t.quantity),  # F-16
        revenue_share_percent=_divide(t.revenue, total_revenue, HUNDRED),  # F-17
    )


@dataclass(frozen=True)
class RevenueBreakdown:
    revenue: Decimal
    items: list[BuyerRevenue]
    subtotals: dict[str, SalesTotals] = field(default_factory=dict)


def revenue_breakdown(buyers: Sequence[BuyerTotals]) -> RevenueBreakdown:
    """Faturamento por comprador e subtotais por tipo (R-FAT-2, R-FAT-3)."""
    total = sum((b.totals.revenue for b in buyers), ZERO)
    subtotals = {t: SalesTotals() for t in BUYER_TYPES}
    for b in buyers:
        subtotals[b.buyer_type] = subtotals[b.buyer_type] + b.totals
    return RevenueBreakdown(revenue=total, items=[buyer_revenue(b, total) for b in buyers], subtotals=subtotals)
