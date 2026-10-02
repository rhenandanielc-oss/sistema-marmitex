"""Schemas de cadastros: empresas, clientes avulsos e categorias de custo."""

from datetime import date, datetime
from typing import Any

from pydantic import EmailStr, Field, field_validator, model_validator

from app.models.enums import CompanyBillingCycle, CostType, CustomerBillingCycle
from app.schemas.common import InputModel, OutputModel
from app.services.validators import is_valid_cnpj, is_valid_cpf, only_digits


def _blank_to_none(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: (None if isinstance(v, str) and not v.strip() else v) for k, v in data.items()}
    return data


class _RegistryIn(InputModel):
    @model_validator(mode="before")
    @classmethod
    def _blanks(cls, data: Any) -> Any:
        return _blank_to_none(data)


# ---------- Empresas ----------

class _CompanyFields(_RegistryIn):
    trade_name: str | None = Field(None, max_length=150)
    cnpj: str | None = Field(None, max_length=18)
    contact_name: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    location: str | None = Field(None, max_length=150)
    start_date: date | None = None
    payment_date: date | None = None
    notes: str | None = Field(None, max_length=2000)

    @field_validator("cnpj")
    @classmethod
    def _cnpj(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not is_valid_cnpj(v):
            raise ValueError("CNPJ inválido.")
        return only_digits(v)


class CompanyCreate(_CompanyFields):
    name: str = Field(min_length=2, max_length=150)
    billing_cycle: CompanyBillingCycle = CompanyBillingCycle.MENSAL


class CompanyUpdate(_CompanyFields):
    name: str | None = Field(None, min_length=2, max_length=150)
    billing_cycle: CompanyBillingCycle | None = None
    version: int = Field(ge=1)


class CompanyRead(OutputModel):
    id: int
    name: str
    trade_name: str | None
    cnpj: str | None
    contact_name: str | None
    phone: str | None
    email: str | None
    location: str | None
    billing_cycle: str
    start_date: date | None
    payment_date: date | None
    notes: str | None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


# ---------- Clientes avulsos ----------

class _CustomerFields(_RegistryIn):
    phone: str | None = Field(None, max_length=20)
    document: str | None = Field(None, max_length=18)
    location: str | None = Field(None, max_length=150)
    start_date: date | None = None
    payment_date: date | None = None
    notes: str | None = Field(None, max_length=2000)

    @field_validator("document")
    @classmethod
    def _document(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = only_digits(v)
        if len(digits) == 11 and is_valid_cpf(digits):
            return digits
        if len(digits) == 14 and is_valid_cnpj(digits):
            return digits
        raise ValueError("CPF/CNPJ inválido.")


class CustomerCreate(_CustomerFields):
    name: str = Field(min_length=2, max_length=150)
    billing_cycle: CustomerBillingCycle = CustomerBillingCycle.MENSAL


class CustomerUpdate(_CustomerFields):
    name: str | None = Field(None, min_length=2, max_length=150)
    billing_cycle: CustomerBillingCycle | None = None
    version: int = Field(ge=1)


class CustomerRead(OutputModel):
    id: int
    name: str
    phone: str | None
    document: str | None
    location: str | None
    billing_cycle: str
    start_date: date | None
    payment_date: date | None
    notes: str | None
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


# ---------- Categorias de custo ----------

class CategoryCreate(_RegistryIn):
    name: str = Field(min_length=2, max_length=80)
    cost_type: CostType


class CategoryUpdate(_RegistryIn):
    name: str | None = Field(None, min_length=2, max_length=80)
    cost_type: CostType | None = None
    version: int = Field(ge=1)


class CategoryRead(OutputModel):
    id: int
    name: str
    cost_type: str
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
