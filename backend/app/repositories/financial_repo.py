"""Agregações financeiras no PostgreSQL (DATABASE.md seção 5).

Todas as consultas usam intervalo fechado [start, end] e ignoram lançamentos excluídos logicamente.
"""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models import Company, Cost, Customer, Sale
from app.models.enums import BuyerType, CostType, PaymentStatus
from app.services.financial_engine import ZERO, BuyerTotals, CostTotals, SalesTotals


def _sales_filters(start: date, end: date, buyer_type: str | None = None, company_id: int | None = None,
                   customer_id: int | None = None, payment_status: str | None = None,
                   delivery_type: str | None = None) -> list[Any]:
    filters: list[Any] = [Sale.deleted_at.is_(None), Sale.sale_date.between(start, end)]
    if buyer_type:
        filters.append(Sale.buyer_type == buyer_type)
    if company_id is not None:
        filters.append(Sale.company_id == company_id)
    if customer_id is not None:
        filters.append(Sale.customer_id == customer_id)
    if payment_status:
        filters.append(Sale.payment_status == payment_status)
    if delivery_type:
        filters.append(Sale.delivery_type == delivery_type)
    return filters


def _to_sales(revenue: Decimal | None, quantity: int | None, count: int | None) -> SalesTotals:
    return SalesTotals(revenue=revenue if revenue is not None else ZERO, quantity=int(quantity or 0),
                       sales_count=int(count or 0))


def sales_totals(db: Session, start: date, end: date, **filters: object) -> SalesTotals:
    row = db.execute(
        select(func.sum(Sale.subtotal), func.sum(Sale.quantity), func.count(Sale.id))
        .where(*_sales_filters(start, end, **filters))  # type: ignore[arg-type]
    ).one()
    return _to_sales(*row)


def sales_totals_by_type(db: Session, start: date, end: date) -> dict[str, SalesTotals]:
    rows = db.execute(
        select(Sale.buyer_type, func.sum(Sale.subtotal), func.sum(Sale.quantity), func.count(Sale.id))
        .where(*_sales_filters(start, end)).group_by(Sale.buyer_type)
    ).all()
    return {r[0]: _to_sales(r[1], r[2], r[3]) for r in rows}


def daily_sales(db: Session, start: date, end: date, **filters: object) -> dict[date, SalesTotals]:
    rows = db.execute(
        select(Sale.sale_date, func.sum(Sale.subtotal), func.sum(Sale.quantity), func.count(Sale.id))
        .where(*_sales_filters(start, end, **filters))  # type: ignore[arg-type]
        .group_by(Sale.sale_date)
    ).all()
    return {r[0]: _to_sales(r[1], r[2], r[3]) for r in rows}


def _cost_sums() -> tuple:
    daily = func.coalesce(func.sum(case((Cost.cost_type == CostType.CUSTO_DIARIO, Cost.amount))), 0)
    fixed = func.coalesce(func.sum(case((Cost.cost_type == CostType.CUSTO_FIXO, Cost.amount))), 0)
    return daily, fixed, func.count(Cost.id)


def cost_filters(start: date, end: date, cost_type: str | None = None, category_id: int | None = None) -> list[Any]:
    filters: list[Any] = [Cost.deleted_at.is_(None), Cost.cost_date.between(start, end)]
    if cost_type:
        filters.append(Cost.cost_type == cost_type)
    if category_id is not None:
        filters.append(Cost.category_id == category_id)
    return filters


def cost_totals(db: Session, start: date, end: date, cost_type: str | None = None,
                category_id: int | None = None) -> CostTotals:
    daily, fixed, count = db.execute(select(*_cost_sums()).where(*cost_filters(start, end, cost_type,
                                                                               category_id))).one()
    return CostTotals(daily=Decimal(daily).quantize(ZERO), fixed=Decimal(fixed).quantize(ZERO), count=int(count))


def daily_costs(db: Session, start: date, end: date) -> dict[date, CostTotals]:
    rows = db.execute(
        select(Cost.cost_date, *_cost_sums()).where(*cost_filters(start, end)).group_by(Cost.cost_date)
    ).all()
    return {r[0]: CostTotals(daily=Decimal(r[1]).quantize(ZERO), fixed=Decimal(r[2]).quantize(ZERO),
                             count=int(r[3])) for r in rows}


def sales_by_buyer(db: Session, start: date, end: date, buyer_type: str | None = None) -> list[BuyerTotals]:
    """Faturamento agrupado por comprador (empresa ou cliente), com o nome do comprador."""
    result: list[BuyerTotals] = []
    sources: Sequence[tuple[str, type, object]] = (
        (BuyerType.COMPANY, Company, Sale.company_id),
        (BuyerType.CUSTOMER, Customer, Sale.customer_id),
    )
    for btype, model, fk in sources:
        if buyer_type and buyer_type != btype:
            continue
        rows = db.execute(
            select(model.id, model.name, func.sum(Sale.subtotal), func.sum(Sale.quantity),  # type: ignore[attr-defined]
                   func.count(Sale.id),
                   func.coalesce(func.sum(Sale.subtotal).filter(Sale.payment_status == PaymentStatus.PENDENTE), 0))
            .join(Sale, and_(fk == model.id, *_sales_filters(start, end, buyer_type=btype)))  # type: ignore[attr-defined]
            .group_by(model.id, model.name)  # type: ignore[attr-defined]
        ).all()
        result.extend(BuyerTotals(buyer_type=str(btype), buyer_id=r[0], name=r[1], totals=_to_sales(r[2], r[3], r[4]),
                                  pending_revenue=Decimal(r[5]).quantize(ZERO)) for r in rows)
    return result


def daily_revenue_by_company(db: Session, start: date, end: date) -> dict[tuple[date, int], Decimal]:
    """Receita por (dia, empresa) — gráfico "histórico de vendas por empresa"."""
    rows = db.execute(
        select(Sale.sale_date, Sale.company_id, func.sum(Sale.subtotal))
        .where(*_sales_filters(start, end, buyer_type=BuyerType.COMPANY))
        .group_by(Sale.sale_date, Sale.company_id)
    ).all()
    return {(r[0], r[1]): r[2] for r in rows}
