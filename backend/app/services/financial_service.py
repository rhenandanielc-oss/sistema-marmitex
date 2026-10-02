"""Serviço financeiro: combina agregados do banco (financial_repo) com as fórmulas (financial_engine).

Base para o dashboard e o histórico (expostos pela API na Fase 3).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Company, Customer, Sale
from app.models.enums import BuyerType
from app.repositories import financial_repo
from app.services import financial_engine as fe
from app.services.periods import Period, ensure_series_limit, previous_period


def summary(db: Session, period: Period) -> fe.FinancialSummary:
    """Indicadores gerais: todas as vendas (empresas + clientes) e todos os custos."""
    sales = financial_repo.sales_totals_by_type(db, period.start_date, period.end_date)
    costs = financial_repo.cost_totals(db, period.start_date, period.end_date)
    return fe.summarize(sales, costs)


def daily(db: Session, period: Period) -> list[fe.DayResult]:
    ensure_series_limit(period)
    return fe.daily_series(
        list(period.iter_days()),
        financial_repo.daily_sales(db, period.start_date, period.end_date),
        financial_repo.daily_costs(db, period.start_date, period.end_date),
    )


SORT_KEYS = {
    "revenue": lambda b: b.revenue,
    "quantity": lambda b: b.quantity,
    "sales_count": lambda b: b.sales_count,
    "name": lambda b: b.name.lower(),
}


def revenue_by_buyer(db: Session, period: Period, buyer_type: str | None = None, sort: str = "revenue",
                     order: str = "desc") -> fe.RevenueBreakdown:
    """Faturamento por comprador. Participação (%) sempre sobre a receita total do período."""
    all_buyers = financial_repo.sales_by_buyer(db, period.start_date, period.end_date)
    breakdown = fe.revenue_breakdown(all_buyers)
    items = [i for i in breakdown.items if buyer_type is None or i.buyer_type == buyer_type]
    key = SORT_KEYS.get(sort, SORT_KEYS["revenue"])
    items.sort(key=lambda b: (b.name.lower(), b.buyer_id))
    items.sort(key=key, reverse=order == "desc")  # type: ignore[arg-type]
    return fe.RevenueBreakdown(revenue=breakdown.revenue, items=items, subtotals=breakdown.subtotals)


@dataclass(frozen=True)
class BuyerDetail:
    buyer: Company | Customer
    buyer_type: str
    revenue: fe.BuyerRevenue
    daily: list[tuple[date, fe.SalesTotals]]
    recent_sales: list[Sale]
    previous_period: Period
    previous: fe.SalesTotals
    revenue_change_percent: Decimal | None


def buyer_detail(db: Session, buyer_type: str, buyer_id: int, period: Period, recent_limit: int = 20) -> BuyerDetail:
    """Dashboard detalhado de uma empresa ou cliente avulso — somente faturamento (R-FAT-1)."""
    ensure_series_limit(period)
    buyer: Company | Customer | None = (
        db.get(Company, buyer_id) if buyer_type == BuyerType.COMPANY else db.get(Customer, buyer_id))
    if buyer is None:
        raise NotFound("Empresa não encontrada." if buyer_type == BuyerType.COMPANY else "Cliente não encontrado.")
    key = "company_id" if buyer_type == BuyerType.COMPANY else "customer_id"
    totals = financial_repo.sales_totals(db, period.start_date, period.end_date, **{key: buyer_id})
    total_revenue = financial_repo.sales_totals(db, period.start_date, period.end_date).revenue
    per_day = financial_repo.daily_sales(db, period.start_date, period.end_date, **{key: buyer_id})
    prev = previous_period(period)
    prev_totals = financial_repo.sales_totals(db, prev.start_date, prev.end_date, **{key: buyer_id})
    fk = Sale.company_id if buyer_type == BuyerType.COMPANY else Sale.customer_id
    recent = db.scalars(
        select(Sale).where(fk == buyer_id, Sale.deleted_at.is_(None),
                           Sale.sale_date.between(period.start_date, period.end_date))
        .order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(recent_limit)
    ).unique().all()
    return BuyerDetail(
        buyer=buyer,
        buyer_type=buyer_type,
        revenue=fe.buyer_revenue(fe.BuyerTotals(buyer_type, buyer_id, buyer.name, totals), total_revenue),
        daily=[(d, per_day.get(d, fe.SalesTotals())) for d in period.iter_days()],
        recent_sales=list(recent),
        previous_period=prev,
        previous=prev_totals,
        revenue_change_percent=fe.percent_change(totals.revenue, prev_totals.revenue),
    )
