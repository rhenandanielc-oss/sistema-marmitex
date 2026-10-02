from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuthorMixin, Base, IdMixin, TimestampMixin, VersionMixin
from app.models.cost_category import CostCategory


class Cost(IdMixin, TimestampMixin, VersionMixin, AuthorMixin, Base):
    """Custo geral do restaurante."""

    __tablename__ = "costs"
    __table_args__ = (
        CheckConstraint("cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO')", name="cost_type"),
        CheckConstraint("amount > 0", name="amount_positive"),
        ForeignKeyConstraint(
            ["category_id", "cost_type"], ["cost_categories.id", "cost_categories.cost_type"],
            name="fk_costs_category_type", onupdate="RESTRICT", ondelete="RESTRICT",
        ),
        Index("ix_costs_cost_date", "cost_date", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_costs_type_date", "cost_type", "cost_date", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_costs_category_date", "category_id", "cost_date", postgresql_where=text("deleted_at IS NULL")),
    )

    category_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cost_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cost_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    category: Mapped[CostCategory] = relationship(
        lazy="joined",
        primaryjoin="Cost.category_id == CostCategory.id",
        foreign_keys=[category_id],
        viewonly=True,
    )
