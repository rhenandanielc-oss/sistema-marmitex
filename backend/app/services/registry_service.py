"""Regras de cadastros: empresas, clientes avulsos e categorias de custo."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, ValidationFailed
from app.core.permissions import CurrentUser
from app.models import Company, Cost, CostCategory, Customer
from app.models.enums import AuditAction
from app.schemas.registry import (
    CategoryCreate,
    CategoryUpdate,
    CompanyCreate,
    CompanyUpdate,
    CustomerCreate,
    CustomerUpdate,
)
from app.services import audit
from app.services.common import check_version, commit, flush, get_or_404, paginate, resolve_sort
from app.services.validators import only_digits

_REQUIRED = {"name", "billing_cycle", "cost_type", "default_delivery_type"}


def _apply(entity: Any, data: BaseModel) -> None:
    for key, value in data.model_dump(exclude_unset=True, exclude={"version"}).items():
        if value is None and key in _REQUIRED:
            raise ValidationFailed("Campo obrigatório.", field=key)
        setattr(entity, key, value.value if hasattr(value, "value") else value)


def _create(db: Session, entity: Any, entity_type: str, actor: CurrentUser, conflict: str) -> Any:
    entity.created_by = actor.id
    entity.updated_by = actor.id
    db.add(entity)
    flush(db, conflict)
    audit.record(db, action=AuditAction.CREATE, entity_type=entity_type, entity_id=entity.id, user_id=actor.id,
                 after=audit.snapshot(entity))
    commit(db, conflict)
    return entity


def _update(db: Session, entity: Any, data: BaseModel, entity_type: str, actor: CurrentUser, conflict: str) -> Any:
    check_version(entity, data.version)  # type: ignore[attr-defined]
    before = audit.snapshot(entity)
    _apply(entity, data)
    entity.updated_by = actor.id
    flush(db, conflict)
    audit.record(db, action=AuditAction.UPDATE, entity_type=entity_type, entity_id=entity.id, user_id=actor.id,
                 before=before, after=audit.snapshot(entity))
    commit(db, conflict)
    return entity


def _set_active(db: Session, entity: Any, active: bool, version: int, entity_type: str,
                actor: CurrentUser) -> Any:
    check_version(entity, version)
    if entity.is_active == active:
        return entity
    before = audit.snapshot(entity)
    entity.is_active = active
    entity.updated_by = actor.id
    flush(db)
    audit.record(db, action=AuditAction.ACTIVATE if active else AuditAction.DEACTIVATE, entity_type=entity_type,
                 entity_id=entity.id, user_id=actor.id, before=before, after=audit.snapshot(entity))
    commit(db)
    return entity


# ---------- Empresas ----------

COMPANY_NOT_FOUND = "Empresa não encontrada."
COMPANY_CONFLICT = "Já existe uma empresa com este nome ou CNPJ."
COMPANY_SORTS = {"name": func.lower(Company.name), "created_at": Company.created_at}


def _company_conflicts(db: Session, name: str | None, cnpj: str | None, exclude_id: int | None = None) -> None:
    if name is not None:
        stmt = select(Company.id).where(func.lower(Company.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(Company.id != exclude_id)
        if db.scalar(stmt):
            raise Conflict("Já existe uma empresa com este nome.")
    if cnpj is not None:
        stmt = select(Company.id).where(Company.cnpj == cnpj)
        if exclude_id:
            stmt = stmt.where(Company.id != exclude_id)
        if db.scalar(stmt):
            raise Conflict("Já existe uma empresa com este CNPJ.")


def list_companies(db: Session, *, q: str | None, active: bool | None, billing_cycle: str | None,
                   sort: str | None, order: str, page: int, page_size: int,
                   delivery_type: str | None = None) -> tuple[list[Company], int]:
    stmt = select(Company)
    if q:
        like = f"%{q.strip()}%"
        conditions = [Company.name.ilike(like), Company.trade_name.ilike(like), Company.location.ilike(like)]
        digits = only_digits(q)
        if digits:
            conditions.append(Company.cnpj.like(f"%{digits}%"))
        stmt = stmt.where(or_(*conditions))
    if active is not None:
        stmt = stmt.where(Company.is_active.is_(active))
    if billing_cycle:
        stmt = stmt.where(Company.billing_cycle == billing_cycle)
    if delivery_type:
        stmt = stmt.where(Company.default_delivery_type == delivery_type)
    return paginate(db, stmt, resolve_sort(sort, order, COMPANY_SORTS, "name"), Company.id, page, page_size)


def get_company(db: Session, company_id: int) -> Company:
    return get_or_404(db, Company, company_id, COMPANY_NOT_FOUND)


def create_company(db: Session, data: CompanyCreate, actor: CurrentUser) -> Company:
    _company_conflicts(db, data.name, data.cnpj)
    company = Company()
    _apply(company, data)
    return _create(db, company, "company", actor, COMPANY_CONFLICT)


def update_company(db: Session, company_id: int, data: CompanyUpdate, actor: CurrentUser) -> Company:
    company = get_company(db, company_id)
    _company_conflicts(db, data.name, data.cnpj, exclude_id=company.id)
    return _update(db, company, data, "company", actor, COMPANY_CONFLICT)


def set_company_active(db: Session, company_id: int, active: bool, version: int, actor: CurrentUser) -> Company:
    return _set_active(db, get_company(db, company_id), active, version, "company", actor)


# ---------- Clientes avulsos ----------

CUSTOMER_NOT_FOUND = "Cliente não encontrado."
CUSTOMER_CONFLICT = "Já existe um cliente com este CPF/CNPJ."
CUSTOMER_SORTS = {"name": func.lower(Customer.name), "created_at": Customer.created_at}


def _customer_conflicts(db: Session, document: str | None, exclude_id: int | None = None) -> None:
    if document is None:
        return
    stmt = select(Customer.id).where(Customer.document == document)
    if exclude_id:
        stmt = stmt.where(Customer.id != exclude_id)
    if db.scalar(stmt):
        raise Conflict(CUSTOMER_CONFLICT)


def list_customers(db: Session, *, q: str | None, active: bool | None, billing_cycle: str | None,
                   sort: str | None, order: str, page: int, page_size: int,
                   delivery_type: str | None = None) -> tuple[list[Customer], int]:
    stmt = select(Customer)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Customer.name.ilike(like), Customer.phone.ilike(like),
                              Customer.location.ilike(like)))
    if active is not None:
        stmt = stmt.where(Customer.is_active.is_(active))
    if billing_cycle:
        stmt = stmt.where(Customer.billing_cycle == billing_cycle)
    if delivery_type:
        stmt = stmt.where(Customer.default_delivery_type == delivery_type)
    return paginate(db, stmt, resolve_sort(sort, order, CUSTOMER_SORTS, "name"), Customer.id, page, page_size)


def get_customer(db: Session, customer_id: int) -> Customer:
    return get_or_404(db, Customer, customer_id, CUSTOMER_NOT_FOUND)


def create_customer(db: Session, data: CustomerCreate, actor: CurrentUser) -> Customer:
    _customer_conflicts(db, data.document)
    customer = Customer()
    _apply(customer, data)
    return _create(db, customer, "customer", actor, CUSTOMER_CONFLICT)


def update_customer(db: Session, customer_id: int, data: CustomerUpdate, actor: CurrentUser) -> Customer:
    customer = get_customer(db, customer_id)
    _customer_conflicts(db, data.document, exclude_id=customer.id)
    return _update(db, customer, data, "customer", actor, CUSTOMER_CONFLICT)


def set_customer_active(db: Session, customer_id: int, active: bool, version: int,
                        actor: CurrentUser) -> Customer:
    return _set_active(db, get_customer(db, customer_id), active, version, "customer", actor)


# ---------- Categorias de custo ----------

CATEGORY_NOT_FOUND = "Categoria não encontrada."
CATEGORY_CONFLICT = "Já existe uma categoria com este nome."
CATEGORY_SORTS = {"name": func.lower(CostCategory.name), "cost_type": CostCategory.cost_type}


def _category_conflicts(db: Session, name: str | None, exclude_id: int | None = None) -> None:
    if name is None:
        return
    stmt = select(CostCategory.id).where(func.lower(CostCategory.name) == name.lower())
    if exclude_id:
        stmt = stmt.where(CostCategory.id != exclude_id)
    if db.scalar(stmt):
        raise Conflict(CATEGORY_CONFLICT)


def list_categories(db: Session, *, q: str | None, active: bool | None, cost_type: str | None,
                    sort: str | None, order: str, page: int, page_size: int) -> tuple[list[CostCategory], int]:
    stmt = select(CostCategory)
    if q:
        stmt = stmt.where(CostCategory.name.ilike(f"%{q.strip()}%"))
    if active is not None:
        stmt = stmt.where(CostCategory.is_active.is_(active))
    if cost_type:
        stmt = stmt.where(CostCategory.cost_type == cost_type)
    return paginate(db, stmt, resolve_sort(sort, order, CATEGORY_SORTS, "name"), CostCategory.id, page,
                    page_size)


def get_category(db: Session, category_id: int) -> CostCategory:
    return get_or_404(db, CostCategory, category_id, CATEGORY_NOT_FOUND)


def create_category(db: Session, data: CategoryCreate, actor: CurrentUser) -> CostCategory:
    _category_conflicts(db, data.name)
    category = CostCategory()
    _apply(category, data)
    return _create(db, category, "cost_category", actor, CATEGORY_CONFLICT)


def update_category(db: Session, category_id: int, data: CategoryUpdate, actor: CurrentUser) -> CostCategory:
    category = get_category(db, category_id)
    _category_conflicts(db, data.name, exclude_id=category.id)
    if data.cost_type is not None and data.cost_type != category.cost_type:
        has_costs = db.scalar(select(exists().where(Cost.category_id == category.id)))
        if has_costs:
            raise Conflict("Não é possível alterar o tipo de uma categoria que já possui custos lançados.")
    return _update(db, category, data, "cost_category", actor, CATEGORY_CONFLICT)


def set_category_active(db: Session, category_id: int, active: bool, version: int,
                        actor: CurrentUser) -> CostCategory:
    return _set_active(db, get_category(db, category_id), active, version, "cost_category", actor)
