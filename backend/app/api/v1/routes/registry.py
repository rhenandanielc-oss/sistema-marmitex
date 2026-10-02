"""Rotas de cadastros: empresas, clientes avulsos e categorias de custo."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.permissions import AdminUser, DbSession
from app.models.enums import CompanyBillingCycle, CostType, CustomerBillingCycle, DeliveryType
from app.schemas.common import Page, SortOrder, VersionIn
from app.schemas.registry import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
)
from app.services import registry_service as svc

PageNum = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]

companies = APIRouter(prefix="/companies", tags=["Empresas"])
customers = APIRouter(prefix="/customers", tags=["Clientes avulsos"])
categories = APIRouter(prefix="/cost-categories", tags=["Categorias de custo"])


# ---------- Empresas ----------

@companies.get("", response_model=Page[CompanyRead], summary="Lista empresas (empreiteiras)")
def list_companies(admin: AdminUser, db: DbSession, q: str | None = None, active: bool | None = None,
                   billing_cycle: CompanyBillingCycle | None = None, delivery_type: DeliveryType | None = None,
                   sort: str | None = None, order: SortOrder = "asc", page: PageNum = 1,
                   page_size: PageSize = 20) -> Page[CompanyRead]:
    items, total = svc.list_companies(db, q=q, active=active, billing_cycle=billing_cycle, sort=sort,
                                      order=order, page=page, page_size=page_size, delivery_type=delivery_type)
    return Page.build([CompanyRead.model_validate(i) for i in items], total, page, page_size)


@companies.post("", response_model=CompanyRead, status_code=201, summary="Cria empresa")
def create_company(data: CompanyCreate, admin: AdminUser, db: DbSession) -> CompanyRead:
    return CompanyRead.model_validate(svc.create_company(db, data, admin))


@companies.get("/{company_id}", response_model=CompanyRead, summary="Detalhe da empresa")
def get_company(company_id: int, admin: AdminUser, db: DbSession) -> CompanyRead:
    return CompanyRead.model_validate(svc.get_company(db, company_id))


@companies.patch("/{company_id}", response_model=CompanyRead, summary="Edita empresa")
def update_company(company_id: int, data: CompanyUpdate, admin: AdminUser, db: DbSession) -> CompanyRead:
    return CompanyRead.model_validate(svc.update_company(db, company_id, data, admin))


@companies.post("/{company_id}/activate", response_model=CompanyRead, summary="Ativa empresa")
def activate_company(company_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CompanyRead:
    return CompanyRead.model_validate(svc.set_company_active(db, company_id, True, data.version, admin))


@companies.post("/{company_id}/deactivate", response_model=CompanyRead, summary="Desativa empresa")
def deactivate_company(company_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CompanyRead:
    return CompanyRead.model_validate(svc.set_company_active(db, company_id, False, data.version, admin))


# ---------- Clientes avulsos ----------

@customers.get("", response_model=Page[CustomerRead], summary="Lista clientes avulsos")
def list_customers(admin: AdminUser, db: DbSession, q: str | None = None, active: bool | None = None,
                   billing_cycle: CustomerBillingCycle | None = None, delivery_type: DeliveryType | None = None,
                   sort: str | None = None, order: SortOrder = "asc", page: PageNum = 1,
                   page_size: PageSize = 20) -> Page[CustomerRead]:
    items, total = svc.list_customers(db, q=q, active=active, billing_cycle=billing_cycle, sort=sort,
                                      order=order, page=page, page_size=page_size, delivery_type=delivery_type)
    return Page.build([CustomerRead.model_validate(i) for i in items], total, page, page_size)


@customers.post("", response_model=CustomerRead, status_code=201, summary="Cria cliente avulso")
def create_customer(data: CustomerCreate, admin: AdminUser, db: DbSession) -> CustomerRead:
    return CustomerRead.model_validate(svc.create_customer(db, data, admin))


@customers.get("/{customer_id}", response_model=CustomerRead, summary="Detalhe do cliente")
def get_customer(customer_id: int, admin: AdminUser, db: DbSession) -> CustomerRead:
    return CustomerRead.model_validate(svc.get_customer(db, customer_id))


@customers.patch("/{customer_id}", response_model=CustomerRead, summary="Edita cliente")
def update_customer(customer_id: int, data: CustomerUpdate, admin: AdminUser, db: DbSession) -> CustomerRead:
    return CustomerRead.model_validate(svc.update_customer(db, customer_id, data, admin))


@customers.post("/{customer_id}/activate", response_model=CustomerRead, summary="Ativa cliente")
def activate_customer(customer_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CustomerRead:
    return CustomerRead.model_validate(svc.set_customer_active(db, customer_id, True, data.version, admin))


@customers.post("/{customer_id}/deactivate", response_model=CustomerRead, summary="Desativa cliente")
def deactivate_customer(customer_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CustomerRead:
    return CustomerRead.model_validate(svc.set_customer_active(db, customer_id, False, data.version, admin))


# ---------- Categorias de custo ----------

@categories.get("", response_model=Page[CategoryRead], summary="Lista categorias (tipos) de custo")
def list_categories(admin: AdminUser, db: DbSession, q: str | None = None, active: bool | None = None,
                    cost_type: CostType | None = None, sort: str | None = None, order: SortOrder = "asc",
                    page: PageNum = 1, page_size: PageSize = 20) -> Page[CategoryRead]:
    items, total = svc.list_categories(db, q=q, active=active, cost_type=cost_type, sort=sort, order=order,
                                       page=page, page_size=page_size)
    return Page.build([CategoryRead.model_validate(i) for i in items], total, page, page_size)


@categories.post("", response_model=CategoryRead, status_code=201, summary="Cria categoria de custo")
def create_category(data: CategoryCreate, admin: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(svc.create_category(db, data, admin))


@categories.get("/{category_id}", response_model=CategoryRead, summary="Detalhe da categoria")
def get_category(category_id: int, admin: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(svc.get_category(db, category_id))


@categories.patch("/{category_id}", response_model=CategoryRead, summary="Edita categoria")
def update_category(category_id: int, data: CategoryUpdate, admin: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(svc.update_category(db, category_id, data, admin))


@categories.post("/{category_id}/activate", response_model=CategoryRead, summary="Ativa categoria")
def activate_category(category_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(svc.set_category_active(db, category_id, True, data.version, admin))


@categories.post("/{category_id}/deactivate", response_model=CategoryRead, summary="Desativa categoria")
def deactivate_category(category_id: int, data: VersionIn, admin: AdminUser, db: DbSession) -> CategoryRead:
    return CategoryRead.model_validate(svc.set_category_active(db, category_id, False, data.version, admin))
