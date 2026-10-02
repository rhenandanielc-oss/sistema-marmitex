"""Regras de lançamentos: vendas e custos (FINANCIAL-RULES.md seções 3 e 4)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import ValidationFailed
from app.core.permissions import CurrentUser
from app.models import Company, Cost, CostCategory, Customer, Sale
from app.models.enums import AuditAction, BuyerType
from app.repositories import financial_repo
from app.schemas.entries import CostCreate, CostUpdate, SaleCreate, SaleUpdate
from app.services import audit
from app.services.common import check_version, commit, flush, get_or_404, resolve_sort
from app.services.financial_engine import CostTotals, sale_subtotal
from app.services.periods import Period

SALE_NOT_FOUND = "Venda não encontrada."
COST_NOT_FOUND = "Custo não encontrado."


def _check_date(value: date, field: str) -> date:
    """R-VEN-4 / R-CUS-4: data escolhida pelo ADMIN, nunca futura."""
    if value > clock.today():
        raise ValidationFailed("A data não pode ser futura.", field=field)
    return value


def _active_buyer(db: Session, buyer_type: str, buyer_id: int) -> Company | Customer:
    field = "company_id" if buyer_type == BuyerType.COMPANY else "customer_id"
    label = "Empresa" if buyer_type == BuyerType.COMPANY else "Cliente"
    buyer: Company | Customer | None = (
        db.get(Company, buyer_id) if buyer_type == BuyerType.COMPANY else db.get(Customer, buyer_id))
    if buyer is None:
        raise ValidationFailed(f"{label} não encontrado(a).", field=field)
    if not buyer.is_active:
        raise ValidationFailed(f"{label} inativo(a) não pode receber novos lançamentos.", field=field)
    return buyer


# ---------- Vendas ----------

def get_sale(db: Session, sale_id: int) -> Sale:
    return get_or_404(db, Sale, sale_id, SALE_NOT_FOUND)


def create_sale(db: Session, data: SaleCreate, actor: CurrentUser) -> Sale:
    buyer_id = data.company_id if data.buyer_type == BuyerType.COMPANY else data.customer_id
    assert buyer_id is not None  # garantido pelo schema
    buyer = _active_buyer(db, data.buyer_type, buyer_id)
    sale = Sale(
        buyer_type=data.buyer_type.value,
        company_id=data.company_id,
        customer_id=data.customer_id,
        sale_date=_check_date(data.sale_date or clock.today(), "sale_date"),
        unit_price=data.unit_price,
        quantity=data.quantity,
        subtotal=sale_subtotal(data.unit_price, data.quantity),
        delivery_type=(data.delivery_type.value if data.delivery_type else buyer.default_delivery_type),
        payment_status=data.payment_status.value,
        notes=data.notes,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(sale)
    flush(db)
    audit.record(db, action=AuditAction.CREATE, entity_type="sale", entity_id=sale.id, user_id=actor.id,
                 after=audit.snapshot(sale))
    commit(db)
    return sale


def update_sale(db: Session, sale_id: int, data: SaleUpdate, actor: CurrentUser) -> Sale:
    sale = get_sale(db, sale_id)
    check_version(sale, data.version)
    before = audit.snapshot(sale)
    fields = data.model_fields_set

    if fields & {"buyer_type", "company_id", "customer_id"}:
        new_type = data.buyer_type.value if data.buyer_type else sale.buyer_type
        if new_type == BuyerType.COMPANY:
            new_id = data.company_id if data.company_id is not None else (
                sale.company_id if sale.buyer_type == BuyerType.COMPANY else None)
            if new_id is None:
                raise ValidationFailed("Informe a empresa.", field="company_id")
            if data.customer_id is not None:
                raise ValidationFailed("Venda para empresa não pode ter cliente.", field="customer_id")
            changed = new_id != sale.company_id or sale.buyer_type != new_type
            new_company, new_customer = new_id, None
        else:
            new_id = data.customer_id if data.customer_id is not None else (
                sale.customer_id if sale.buyer_type == BuyerType.CUSTOMER else None)
            if new_id is None:
                raise ValidationFailed("Informe o cliente.", field="customer_id")
            if data.company_id is not None:
                raise ValidationFailed("Venda para cliente avulso não pode ter empresa.", field="company_id")
            changed = new_id != sale.customer_id or sale.buyer_type != new_type
            new_company, new_customer = None, new_id
        if changed:  # R-VEN-7: trocar de comprador exige comprador ativo
            _active_buyer(db, new_type, new_id)
        sale.buyer_type, sale.company_id, sale.customer_id = new_type, new_company, new_customer

    if "sale_date" in fields and data.sale_date is not None:
        sale.sale_date = _check_date(data.sale_date, "sale_date")
    if "unit_price" in fields and data.unit_price is not None:
        sale.unit_price = data.unit_price
    if "quantity" in fields and data.quantity is not None:
        sale.quantity = data.quantity
    if "delivery_type" in fields and data.delivery_type is not None:
        sale.delivery_type = data.delivery_type.value
    if "payment_status" in fields and data.payment_status is not None:
        sale.payment_status = data.payment_status.value
    if "notes" in fields:
        sale.notes = data.notes
    sale.subtotal = sale_subtotal(sale.unit_price, sale.quantity)  # R-VEN-6
    sale.updated_by = actor.id
    flush(db)
    audit.record(db, action=AuditAction.UPDATE, entity_type="sale", entity_id=sale.id, user_id=actor.id,
                 before=before, after=audit.snapshot(sale))
    commit(db)
    db.refresh(sale)
    return sale


def delete_sale(db: Session, sale_id: int, actor: CurrentUser) -> None:
    sale = get_sale(db, sale_id)
    before = audit.snapshot(sale)
    sale.deleted_at = clock.now()
    sale.deleted_by = actor.id
    flush(db)
    audit.record(db, action=AuditAction.DELETE, entity_type="sale", entity_id=sale.id, user_id=actor.id,
                 before=before, after=audit.snapshot(sale))
    commit(db)


def _buyer_name_expr() -> Any:
    company_name = select(Company.name).where(Company.id == Sale.company_id).scalar_subquery()
    customer_name = select(Customer.name).where(Customer.id == Sale.customer_id).scalar_subquery()
    return func.lower(func.coalesce(company_name, customer_name))


SALE_SORTS = {"sale_date": Sale.sale_date, "subtotal": Sale.subtotal, "quantity": Sale.quantity,
              "buyer": _buyer_name_expr()}


def list_sales(db: Session, *, start_date: date | None, end_date: date | None, buyer_type: str | None,
               company_id: int | None, customer_id: int | None, sort: str | None, order: str, page: int,
               page_size: int, payment_status: str | None = None,
               delivery_type: str | None = None) -> tuple[list[Sale], int]:
    stmt = select(Sale).where(Sale.deleted_at.is_(None))
    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)
    if buyer_type:
        stmt = stmt.where(Sale.buyer_type == buyer_type)
    if company_id is not None:
        stmt = stmt.where(Sale.company_id == company_id)
    if customer_id is not None:
        stmt = stmt.where(Sale.customer_id == customer_id)
    if payment_status:
        stmt = stmt.where(Sale.payment_status == payment_status)
    if delivery_type:
        stmt = stmt.where(Sale.delivery_type == delivery_type)
    order_by = resolve_sort(sort, order, SALE_SORTS, "sale_date")
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(*order_by, Sale.id.desc()).offset((page - 1) * page_size)
                      .limit(page_size)).unique().all()
    return list(rows), total


# ---------- Custos ----------

def get_cost(db: Session, cost_id: int) -> Cost:
    return get_or_404(db, Cost, cost_id, COST_NOT_FOUND)


def _category_for(db: Session, category_id: int, cost_type: str, require_active: bool) -> CostCategory:
    category = db.get(CostCategory, category_id)
    if category is None:
        raise ValidationFailed("Categoria não encontrada.", field="category_id")
    if require_active and not category.is_active:
        raise ValidationFailed("Categoria inativa não pode receber novos lançamentos.", field="category_id")
    if category.cost_type != cost_type:  # R-CUS-3
        raise ValidationFailed("O tipo do custo deve ser igual ao tipo da categoria.", field="cost_type")
    return category


def create_cost(db: Session, data: CostCreate, actor: CurrentUser) -> Cost:
    _category_for(db, data.category_id, data.cost_type.value, require_active=True)
    cost = Cost(
        category_id=data.category_id,
        cost_type=data.cost_type.value,
        cost_date=_check_date(data.cost_date or clock.today(), "cost_date"),
        amount=data.amount,
        description=data.description,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(cost)
    flush(db)
    audit.record(db, action=AuditAction.CREATE, entity_type="cost", entity_id=cost.id, user_id=actor.id,
                 after=audit.snapshot(cost))
    commit(db)
    db.refresh(cost)
    return cost


def update_cost(db: Session, cost_id: int, data: CostUpdate, actor: CurrentUser) -> Cost:
    cost = get_cost(db, cost_id)
    check_version(cost, data.version)
    before = audit.snapshot(cost)
    fields = data.model_fields_set
    new_category = data.category_id if "category_id" in fields and data.category_id else cost.category_id
    new_type = data.cost_type.value if "cost_type" in fields and data.cost_type else cost.cost_type
    if new_category != cost.category_id or new_type != cost.cost_type:
        # R-CUS-2: manter a categoria atual é permitido mesmo se desativada; trocar exige categoria ativa.
        _category_for(db, new_category, new_type, require_active=new_category != cost.category_id)
    cost.category_id, cost.cost_type = new_category, new_type
    if "cost_date" in fields and data.cost_date is not None:
        cost.cost_date = _check_date(data.cost_date, "cost_date")
    if "amount" in fields and data.amount is not None:
        cost.amount = data.amount
    if "description" in fields:
        cost.description = data.description
    cost.updated_by = actor.id
    flush(db)
    audit.record(db, action=AuditAction.UPDATE, entity_type="cost", entity_id=cost.id, user_id=actor.id,
                 before=before, after=audit.snapshot(cost))
    commit(db)
    db.refresh(cost)
    return cost


def delete_cost(db: Session, cost_id: int, actor: CurrentUser) -> None:
    cost = get_cost(db, cost_id)
    before = audit.snapshot(cost)
    cost.deleted_at = clock.now()
    cost.deleted_by = actor.id
    flush(db)
    audit.record(db, action=AuditAction.DELETE, entity_type="cost", entity_id=cost.id, user_id=actor.id,
                 before=before, after=audit.snapshot(cost))
    commit(db)


COST_SORTS: dict[str, Any] = {
    "cost_date": Cost.cost_date,
    "amount": Cost.amount,
    "category": select(func.lower(CostCategory.name)).where(CostCategory.id == Cost.category_id).scalar_subquery(),
}


@dataclass
class CostListResult:
    items: list[tuple[Cost, Decimal]]
    total: int
    totals: CostTotals


def list_costs(db: Session, *, start_date: date | None, end_date: date | None, cost_type: str | None,
               category_id: int | None, sort: str | None, order: str, page: int, page_size: int) -> CostListResult:
    """Lista custos com acumulado cronológico (R-CUS-7) e totais do filtro."""
    start = start_date or date.min
    end = end_date or date.max
    filters = financial_repo.cost_filters(start, end, cost_type, category_id)
    running = (
        select(Cost.id.label("id"),
               func.sum(Cost.amount).over(order_by=(Cost.cost_date, Cost.id)).label("running_total"))
        .where(*filters).subquery()
    )
    order_by = resolve_sort(sort, order, COST_SORTS, "cost_date")
    rows = db.execute(
        select(Cost, running.c.running_total).join(running, running.c.id == Cost.id)
        .order_by(*order_by, Cost.id.desc() if order == "desc" else Cost.id.asc())
        .offset((page - 1) * page_size).limit(page_size)
    ).unique().all()
    totals = financial_repo.cost_totals(db, start, end, cost_type, category_id)
    return CostListResult(items=[(r[0], r[1]) for r in rows], total=totals.count, totals=totals)


def cost_summary(db: Session, period: Period) -> CostTotals:
    """R-CUS-8: totais de custos do período (padrão: mês corrente até hoje)."""
    return financial_repo.cost_totals(db, period.start_date, period.end_date)
