"""Rotas de lançamentos: vendas e custos."""

from datetime import date
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.core import clock
from app.core.permissions import AdminUser, DbSession
from app.models.enums import BuyerType, CostType
from app.schemas.common import Page, SortOrder
from app.schemas.entries import (
    CostCreate,
    CostListItem,
    CostPage,
    CostRead,
    CostSummaryOut,
    CostTotalsOut,
    CostUpdate,
    PeriodOut,
    SaleCreate,
    SaleRead,
    SaleUpdate,
)
from app.services import entries_service as svc
from app.services.financial_engine import CostTotals
from app.services.periods import PeriodPreset, resolve_period

PageNum = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]

sales = APIRouter(prefix="/sales", tags=["Vendas"])
costs = APIRouter(prefix="/costs", tags=["Custos"])


def _totals_out(t: CostTotals) -> CostTotalsOut:
    return CostTotalsOut(daily_costs=t.daily, fixed_costs=t.fixed, total_costs=t.total, count=t.count)


# ---------- Vendas ----------

@sales.get("", response_model=Page[SaleRead], summary="Lista vendas")
def list_sales(admin: AdminUser, db: DbSession, start_date: date | None = None, end_date: date | None = None,
               buyer_type: BuyerType | None = None, company_id: int | None = None, customer_id: int | None = None,
               sort: str | None = None, order: SortOrder = "desc", page: PageNum = 1,
               page_size: PageSize = 20) -> Page[SaleRead]:
    items, total = svc.list_sales(db, start_date=start_date, end_date=end_date, buyer_type=buyer_type,
                                  company_id=company_id, customer_id=customer_id, sort=sort, order=order,
                                  page=page, page_size=page_size)
    return Page.build([SaleRead.from_model(s) for s in items], total, page, page_size)


@sales.post("", response_model=SaleRead, status_code=201, summary="Lança venda (data padrão: hoje)")
def create_sale(data: SaleCreate, admin: AdminUser, db: DbSession) -> SaleRead:
    return SaleRead.from_model(svc.create_sale(db, data, admin))


@sales.get("/{sale_id}", response_model=SaleRead, summary="Detalhe da venda")
def get_sale(sale_id: int, admin: AdminUser, db: DbSession) -> SaleRead:
    return SaleRead.from_model(svc.get_sale(db, sale_id))


@sales.patch("/{sale_id}", response_model=SaleRead, summary="Edita venda (subtotal recalculado)")
def update_sale(sale_id: int, data: SaleUpdate, admin: AdminUser, db: DbSession) -> SaleRead:
    return SaleRead.from_model(svc.update_sale(db, sale_id, data, admin))


@sales.delete("/{sale_id}", status_code=204, summary="Exclui venda (exclusão lógica)")
def delete_sale(sale_id: int, admin: AdminUser, db: DbSession) -> Response:
    svc.delete_sale(db, sale_id, admin)
    return Response(status_code=204)


# ---------- Custos ----------

@costs.get("", response_model=CostPage, summary="Lista custos com acumulado")
def list_costs(admin: AdminUser, db: DbSession, start_date: date | None = None, end_date: date | None = None,
               cost_type: CostType | None = None, category_id: int | None = None, sort: str | None = None,
               order: SortOrder = "desc", page: PageNum = 1, page_size: PageSize = 20) -> CostPage:
    result = svc.list_costs(db, start_date=start_date, end_date=end_date, cost_type=cost_type,
                            category_id=category_id, sort=sort, order=order, page=page, page_size=page_size)
    items = [CostListItem(**CostRead.from_model(c).model_dump(), running_total=rt) for c, rt in result.items]
    return CostPage(items=items, total=result.total, page=page, page_size=page_size,
                    pages=ceil(result.total / page_size) if result.total else 0, totals=_totals_out(result.totals))


@costs.get("/summary", response_model=CostSummaryOut, summary="Totais de custos do período (padrão: mês atual)")
def cost_summary(admin: AdminUser, db: DbSession, period: PeriodPreset = PeriodPreset.MONTH,
                 start_date: date | None = None, end_date: date | None = None) -> CostSummaryOut:
    p = resolve_period(period, start_date, end_date, clock.today())
    totals = _totals_out(svc.cost_summary(db, p))
    return CostSummaryOut(**totals.model_dump(), period=PeriodOut(preset=p.preset, start_date=p.start_date,
                                                                   end_date=p.end_date, days=p.days))


@costs.post("", response_model=CostRead, status_code=201, summary="Lança custo (data padrão: hoje)")
def create_cost(data: CostCreate, admin: AdminUser, db: DbSession) -> CostRead:
    return CostRead.from_model(svc.create_cost(db, data, admin))


@costs.get("/{cost_id}", response_model=CostRead, summary="Detalhe do custo")
def get_cost(cost_id: int, admin: AdminUser, db: DbSession) -> CostRead:
    return CostRead.from_model(svc.get_cost(db, cost_id))


@costs.patch("/{cost_id}", response_model=CostRead, summary="Edita custo")
def update_cost(cost_id: int, data: CostUpdate, admin: AdminUser, db: DbSession) -> CostRead:
    return CostRead.from_model(svc.update_cost(db, cost_id, data, admin))


@costs.delete("/{cost_id}", status_code=204, summary="Exclui custo (exclusão lógica)")
def delete_cost(cost_id: int, admin: AdminUser, db: DbSession) -> Response:
    svc.delete_cost(db, cost_id, admin)
    return Response(status_code=204)
