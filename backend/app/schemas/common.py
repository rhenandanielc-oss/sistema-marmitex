from decimal import Decimal
from math import ceil
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

T = TypeVar("T")

CENT = Decimal("0.01")


def money_str(value: Decimal) -> str:
    return f"{value.quantize(CENT):.2f}"


# Dinheiro: Decimal com no máximo 2 casas na entrada; string "1234.50" na saída (FINANCIAL-RULES.md seção 1).
MoneyOut = Annotated[Decimal, PlainSerializer(money_str, return_type=str, when_used="json")]
OptionalMoneyOut = Annotated[
    Decimal | None, PlainSerializer(lambda v: None if v is None else money_str(v), return_type=str | None,
                                    when_used="json")
]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "Page[T]":
        return cls(items=items, total=total, page=page, page_size=page_size,
                   pages=ceil(total / page_size) if total else 0)


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


SortOrder = Literal["asc", "desc"]


class VersionIn(InputModel):
    version: int = Field(ge=1)


class Ref(OutputModel):
    id: int
    name: str
