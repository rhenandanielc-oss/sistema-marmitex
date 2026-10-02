"""Histórico unificado de lançamentos (API.md 3.9)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session

from app.core.errors import ValidationFailed
from app.models import Cost, Sale
from app.repositories import financial_repo
from app.services.financial_engine import CostTotals, SalesTotals


@dataclass
class HistoryFilters:
    type: str = "ALL"
    start_date: date | None = None
    end_date: date | None = None
    buyer_type: str | None = None
    company_id: int | None = None
    customer_id: int | None = None
    cost_type: str | None = None
    category_id: int | None = None
    payment_status: str | None = None
    delivery_type: str | None = None

    @property
    def has_buyer_filter(self) -> bool:
        # Filtros que só existem em vendas (comprador, pagamento, tipo de recebimento).
        return any(v is not None for v in (self.buyer_type, self.company_id, self.customer_id, self.payment_status,
                                           self.delivery_type))

    @property
    def has_cost_filter(self) -> bool:
        return self.cost_type is not None or self.category_id is not None

    @property
    def include_sales(self) -> bool:
        # Filtro de categoria/tipo de custo restringe a custos.
        return self.type in ("ALL", "SALE") and not (self.type == "ALL" and self.has_cost_filter)

    @property
    def include_costs(self) -> bool:
        # Custos não pertencem a comprador: com filtro de comprador, só vendas.
        return self.type in ("ALL", "COST") and not self.has_buyer_filter


@dataclass
class HistoryResult:
    rows: list[tuple[str, Any]]
    total: int
    sales: SalesTotals
    costs: CostTotals
    sales_pending: Decimal = Decimal("0.00")


def _bounds(f: HistoryFilters) -> tuple[date, date]:
    if f.start_date and f.end_date and f.start_date > f.end_date:
        raise ValidationFailed("A data inicial deve ser menor ou igual à data final.", field="start_date")
    return f.start_date or date.min, f.end_date or date.max


def history(db: Session, f: HistoryFilters, sort: str | None, order: str, page: int, page_size: int) -> HistoryResult:
    start, end = _bounds(f)
    parts = []
    sales = SalesTotals()
    costs = CostTotals()
    pending = Decimal("0.00")
    if f.include_sales:
        filters = financial_repo._sales_filters(start, end, f.buyer_type, f.company_id, f.customer_id,
                                                f.payment_status, f.delivery_type)
        parts.append(select(literal("SALE").label("kind"), Sale.id.label("id"), Sale.sale_date.label("date"),
                            Sale.subtotal.label("amount")).where(*filters))
        sales = financial_repo.sales_totals(db, start, end, buyer_type=f.buyer_type, company_id=f.company_id,
                                            customer_id=f.customer_id, payment_status=f.payment_status,
                                            delivery_type=f.delivery_type)
        if f.payment_status in (None, "PENDENTE"):
            pending = financial_repo.sales_totals(db, start, end, buyer_type=f.buyer_type, company_id=f.company_id,
                                                  customer_id=f.customer_id, payment_status="PENDENTE",
                                                  delivery_type=f.delivery_type).revenue
    if f.include_costs:
        filters = financial_repo.cost_filters(start, end, f.cost_type, f.category_id)
        parts.append(select(literal("COST").label("kind"), Cost.id.label("id"), Cost.cost_date.label("date"),
                            Cost.amount.label("amount")).where(*filters))
        costs = financial_repo.cost_totals(db, start, end, f.cost_type, f.category_id)
    if not parts:
        return HistoryResult([], 0, sales, costs, pending)

    entries = (union_all(*parts) if len(parts) > 1 else parts[0]).subquery()
    sort_key = sort or "date"
    if sort_key not in ("date", "amount"):
        raise ValidationFailed("Ordenação inválida. Opções: amount, date.", field="sort")
    column = entries.c[sort_key]
    direction = column.desc() if order == "desc" else column.asc()
    tiebreak = entries.c.id.desc() if order == "desc" else entries.c.id.asc()
    total = db.scalar(select(func.count()).select_from(entries)) or 0
    page_rows = db.execute(
        select(entries.c.kind, entries.c.id).order_by(direction, entries.c.date.desc(), entries.c.kind, tiebreak)
        .offset((page - 1) * page_size).limit(page_size)
    ).all()

    sale_ids = [r.id for r in page_rows if r.kind == "SALE"]
    cost_ids = [r.id for r in page_rows if r.kind == "COST"]
    sale_map = {s.id: s for s in db.scalars(select(Sale).where(Sale.id.in_(sale_ids))).unique()} if sale_ids else {}
    cost_map = {c.id: c for c in db.scalars(select(Cost).where(Cost.id.in_(cost_ids))).unique()} if cost_ids else {}
    rows = [(r.kind, sale_map[r.id] if r.kind == "SALE" else cost_map[r.id]) for r in page_rows]
    return HistoryResult(rows, total, sales, costs, pending)
