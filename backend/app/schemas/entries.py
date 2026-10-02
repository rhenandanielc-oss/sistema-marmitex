"""Schemas de lançamentos: vendas e custos (FINANCIAL-RULES.md seções 3 e 4)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import Field, model_validator

from app.models.enums import BuyerType, CostType
from app.schemas.common import InputModel, MoneyOut, OutputModel, Ref
from app.services.financial_engine import MAX_COST_AMOUNT, MAX_QUANTITY, MAX_UNIT_PRICE

_UNIT_PRICE: dict[str, Any] = {"gt": 0, "le": MAX_UNIT_PRICE, "max_digits": 12, "decimal_places": 2}
_QUANTITY: dict[str, Any] = {"gt": 0, "le": MAX_QUANTITY}
_AMOUNT: dict[str, Any] = {"gt": 0, "le": MAX_COST_AMOUNT, "max_digits": 12, "decimal_places": 2}


def _check_buyer(buyer_type: BuyerType | None, company_id: int | None, customer_id: int | None,
                 partial: bool) -> None:
    if buyer_type is None:
        if partial:
            return
        raise ValueError("Informe o tipo de comprador.")
    if buyer_type == BuyerType.COMPANY:
        if customer_id is not None:
            raise ValueError("Venda para empresa não pode ter cliente.")
        if company_id is None and not partial:
            raise ValueError("Informe a empresa.")
    else:
        if company_id is not None:
            raise ValueError("Venda para cliente avulso não pode ter empresa.")
        if customer_id is None and not partial:
            raise ValueError("Informe o cliente.")


class SaleCreate(InputModel):
    buyer_type: BuyerType
    company_id: int | None = Field(None, ge=1)
    customer_id: int | None = Field(None, ge=1)
    unit_price: Decimal = Field(**_UNIT_PRICE)
    quantity: int = Field(**_QUANTITY)
    sale_date: date | None = None
    notes: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def _single_buyer(self) -> "SaleCreate":
        _check_buyer(self.buyer_type, self.company_id, self.customer_id, partial=False)
        return self


class SaleUpdate(InputModel):
    buyer_type: BuyerType | None = None
    company_id: int | None = Field(None, ge=1)
    customer_id: int | None = Field(None, ge=1)
    unit_price: Decimal | None = Field(None, **_UNIT_PRICE)
    quantity: int | None = Field(None, **_QUANTITY)
    sale_date: date | None = None
    notes: str | None = Field(None, max_length=500)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def _single_buyer(self) -> "SaleUpdate":
        if self.buyer_type is not None or self.company_id is not None or self.customer_id is not None:
            if self.company_id is not None and self.customer_id is not None:
                raise ValueError("A venda deve ter um único comprador: empresa ou cliente.")
            _check_buyer(self.buyer_type, self.company_id, self.customer_id, partial=True)
        for name in ("unit_price", "quantity", "sale_date"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"O campo {name} não pode ser vazio.")
        return self


class BuyerRef(OutputModel):
    type: str
    id: int
    name: str


class SaleRead(OutputModel):
    id: int
    sale_date: date
    buyer_type: str
    buyer: BuyerRef
    unit_price: MoneyOut
    quantity: int
    subtotal: MoneyOut
    notes: str | None
    version: int
    created_at: datetime
    created_by: Ref | None

    @classmethod
    def from_model(cls, sale: Any) -> "SaleRead":
        party = sale.company if sale.buyer_type == BuyerType.COMPANY else sale.customer
        return cls(
            id=sale.id, sale_date=sale.sale_date, buyer_type=sale.buyer_type,
            buyer=BuyerRef(type=sale.buyer_type, id=party.id, name=party.name),
            unit_price=sale.unit_price, quantity=sale.quantity, subtotal=sale.subtotal, notes=sale.notes,
            version=sale.version, created_at=sale.created_at,
            created_by=Ref(id=sale.creator.id, name=sale.creator.name) if sale.creator else None,
        )


class CostCreate(InputModel):
    category_id: int = Field(ge=1)
    cost_type: CostType
    amount: Decimal = Field(**_AMOUNT)
    cost_date: date | None = None
    description: str | None = Field(None, max_length=500)


class CostUpdate(InputModel):
    category_id: int | None = Field(None, ge=1)
    cost_type: CostType | None = None
    amount: Decimal | None = Field(None, **_AMOUNT)
    cost_date: date | None = None
    description: str | None = Field(None, max_length=500)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def _no_null_required(self) -> "CostUpdate":
        for name in ("category_id", "cost_type", "amount", "cost_date"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"O campo {name} não pode ser vazio.")
        return self


class CostRead(OutputModel):
    id: int
    cost_date: date
    category: Ref
    cost_type: str
    amount: MoneyOut
    description: str | None
    version: int
    created_at: datetime
    created_by: Ref | None

    @classmethod
    def from_model(cls, cost: Any) -> "CostRead":
        return cls(
            id=cost.id, cost_date=cost.cost_date, category=Ref(id=cost.category.id, name=cost.category.name),
            cost_type=cost.cost_type, amount=cost.amount, description=cost.description, version=cost.version,
            created_at=cost.created_at,
            created_by=Ref(id=cost.creator.id, name=cost.creator.name) if cost.creator else None,
        )


class CostListItem(CostRead):
    running_total: MoneyOut


class CostTotalsOut(OutputModel):
    daily_costs: MoneyOut
    fixed_costs: MoneyOut
    total_costs: MoneyOut
    count: int


class CostPage(OutputModel):
    items: list[CostListItem]
    total: int
    page: int
    page_size: int
    pages: int
    totals: CostTotalsOut


class PeriodOut(OutputModel):
    preset: str
    start_date: date
    end_date: date
    days: int


class CostSummaryOut(CostTotalsOut):
    period: PeriodOut
