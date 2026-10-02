"""Rotas de histórico e dashboard (API.md 3.9 e 3.10). Todos os valores vêm do backend."""

from datetime import date
from math import ceil
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core import clock
from app.core.permissions import AdminUser, DbSession
from app.models import Company, Cost, Customer, Sale
from app.models.enums import BuyerType, CostType, DeliveryType, PaymentStatus
from app.schemas.common import Ref, SortOrder
from app.schemas.entries import BuyerRef, PeriodOut, SaleRead
from app.schemas.reports import (
    BuyerDailyItem,
    BuyerDashboardOut,
    BuyerInfo,
    BuyerRevenueItem,
    ByBuyerOut,
    CompanySeriesItem,
    ComparisonOut,
    DailyItem,
    DailyOut,
    HistoryCost,
    HistoryItem,
    HistoryPage,
    HistorySale,
    HistoryTotals,
    SalesByCompanyDailyOut,
    Subtotal,
    SummaryOut,
)
from app.services import financial_service as fs
from app.services.history_service import HistoryFilters, history
from app.services.periods import Period, PeriodPreset, resolve_period

history_router = APIRouter(prefix="/history", tags=["Histórico"])
dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def period_param(period: PeriodPreset = PeriodPreset.MONTH, start_date: date | None = None,
                 end_date: date | None = None) -> Period:
    """Período do filtro: hoje, semana, mês (padrão), mês anterior ou personalizado."""
    return resolve_period(period, start_date, end_date, clock.today())


PeriodDep = Annotated[Period, Depends(period_param)]


def _period_out(p: Period) -> PeriodOut:
    return PeriodOut(preset=p.preset, start_date=p.start_date, end_date=p.end_date, days=p.days)


def _buyer_ref(sale: Sale) -> BuyerRef:
    party = sale.company if sale.buyer_type == BuyerType.COMPANY else sale.customer
    assert party is not None
    return BuyerRef(type=sale.buyer_type, id=party.id, name=party.name)


# ---------- Histórico ----------

@history_router.get("", response_model=HistoryPage, summary="Histórico de vendas e custos")
def get_history(
    admin: AdminUser, db: DbSession,
    type: Literal["ALL", "SALE", "COST"] = "ALL",
    start_date: date | None = None, end_date: date | None = None,
    buyer_type: BuyerType | None = None, company_id: int | None = None, customer_id: int | None = None,
    cost_type: CostType | None = None, category_id: int | None = None,
    payment_status: PaymentStatus | None = None, delivery_type: DeliveryType | None = None,
    sort: str | None = None, order: SortOrder = "desc",
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> HistoryPage:
    f = HistoryFilters(type=type, start_date=start_date, end_date=end_date, buyer_type=buyer_type,
                       company_id=company_id, customer_id=customer_id, cost_type=cost_type, category_id=category_id,
                       payment_status=payment_status, delivery_type=delivery_type)
    result = history(db, f, sort, order, page, page_size)
    items = []
    for kind, entity in result.rows:
        if kind == "SALE":
            s: Sale = entity
            items.append(HistoryItem(kind="SALE", id=s.id, date=s.sale_date, amount=s.subtotal, cost=None,
                                     sale=HistorySale(buyer=_buyer_ref(s), quantity=s.quantity,
                                                      unit_price=s.unit_price, subtotal=s.subtotal,
                                                      delivery_type=s.delivery_type,
                                                      payment_status=s.payment_status)))
        else:
            c: Cost = entity
            items.append(HistoryItem(kind="COST", id=c.id, date=c.cost_date, amount=c.amount, sale=None,
                                     cost=HistoryCost(category=Ref(id=c.category.id, name=c.category.name),
                                                      cost_type=c.cost_type, amount=c.amount,
                                                      description=c.description)))
    totals = HistoryTotals(sales_total=result.sales.revenue, sales_quantity=result.sales.quantity,
                           sales_count=result.sales.sales_count, sales_pending_total=result.sales_pending,
                           costs_total=result.costs.total,
                           costs_count=result.costs.count)
    return HistoryPage(items=items, total=result.total, page=page, page_size=page_size,
                       pages=ceil(result.total / page_size) if result.total else 0, totals=totals)


# ---------- Dashboard ----------

@dashboard.get("/summary", response_model=SummaryOut, summary="Indicadores gerais do período")
def summary(admin: AdminUser, db: DbSession, period: PeriodDep) -> SummaryOut:
    s = fs.summary(db, period)
    return SummaryOut(period=_period_out(period), **s.__dict__)


@dashboard.get("/daily", response_model=DailyOut, summary="Série diária (receita, custos, lucro, acumulados)")
def daily(admin: AdminUser, db: DbSession, period: PeriodDep) -> DailyOut:
    return DailyOut(period=_period_out(period), items=[DailyItem(**d.__dict__) for d in fs.daily(db, period)])


@dashboard.get("/by-buyer", response_model=ByBuyerOut, summary="Faturamento por empresa e cliente")
def by_buyer(admin: AdminUser, db: DbSession, period: PeriodDep, buyer_type: BuyerType | None = None,
             sort: Literal["revenue", "quantity", "sales_count", "name"] = "revenue",
             order: SortOrder = "desc") -> ByBuyerOut:
    b = fs.revenue_by_buyer(db, period, buyer_type, sort, order)
    items = [
        BuyerRevenueItem(buyer=BuyerRef(type=i.buyer_type, id=i.buyer_id, name=i.name), revenue=i.revenue,
                         quantity=i.quantity, sales_count=i.sales_count, average_ticket=i.average_ticket,
                         average_price_per_meal=i.average_price_per_meal,
                         revenue_share_percent=i.revenue_share_percent, pending_revenue=i.pending_revenue)
        for i in b.items
    ]
    subtotals = {t: Subtotal(revenue=v.revenue, quantity=v.quantity, sales_count=v.sales_count)
                 for t, v in b.subtotals.items()}
    return ByBuyerOut(period=_period_out(period), revenue=b.revenue, items=items, subtotals=subtotals)


@dashboard.get("/sales-by-company-daily", response_model=SalesByCompanyDailyOut,
               summary="Histórico diário de vendas por empresa")
def sales_by_company_daily(admin: AdminUser, db: DbSession, period: PeriodDep,
                           top: Annotated[int, Query(ge=1, le=10)] = 10) -> SalesByCompanyDailyOut:
    series = fs.sales_by_company_daily(db, period, top=top)
    return SalesByCompanyDailyOut(
        period=_period_out(period),
        companies=[Ref(id=cid, name=name) for cid, name in series.companies],
        has_other_companies=series.has_other_companies,
        items=[CompanySeriesItem(date=d, values={str(k): v for k, v in values.items()}, other_companies=others,
                                 customers=customers) for d, values, others, customers in series.items],
    )


def _buyer_dashboard(db: DbSession, buyer_type: str, buyer_id: int, period: Period) -> BuyerDashboardOut:
    d = fs.buyer_detail(db, buyer_type, buyer_id, period)
    buyer: Company | Customer = d.buyer
    r = d.revenue
    return BuyerDashboardOut(
        period=_period_out(period),
        buyer=BuyerInfo(type=buyer_type, id=buyer.id, name=buyer.name, is_active=buyer.is_active,
                        billing_cycle=buyer.billing_cycle, start_date=buyer.start_date,
                        payment_date=buyer.payment_date),
        revenue=r.revenue, quantity=r.quantity, sales_count=r.sales_count, average_ticket=r.average_ticket,
        average_price_per_meal=r.average_price_per_meal, revenue_share_percent=r.revenue_share_percent,
        pending_revenue=r.pending_revenue,
        daily=[BuyerDailyItem(date=day, revenue=t.revenue, quantity=t.quantity, sales_count=t.sales_count)
               for day, t in d.daily],
        recent_sales=[SaleRead.from_model(s) for s in d.recent_sales],
        comparison=ComparisonOut(previous_period=_period_out(d.previous_period), revenue=d.previous.revenue,
                                 quantity=d.previous.quantity, sales_count=d.previous.sales_count,
                                 revenue_change_percent=d.revenue_change_percent),
    )


@dashboard.get("/companies/{company_id}", response_model=BuyerDashboardOut, summary="Dashboard da empresa")
def company_dashboard(company_id: int, admin: AdminUser, db: DbSession, period: PeriodDep) -> BuyerDashboardOut:
    return _buyer_dashboard(db, BuyerType.COMPANY, company_id, period)


@dashboard.get("/customers/{customer_id}", response_model=BuyerDashboardOut, summary="Dashboard do cliente avulso")
def customer_dashboard(customer_id: int, admin: AdminUser, db: DbSession, period: PeriodDep) -> BuyerDashboardOut:
    return _buyer_dashboard(db, BuyerType.CUSTOMER, customer_id, period)
