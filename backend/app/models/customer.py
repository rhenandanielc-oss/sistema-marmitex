from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuthorMixin, Base, IdMixin, TimestampMixin, VersionMixin


class Customer(IdMixin, TimestampMixin, VersionMixin, AuthorMixin, Base):
    """Cliente avulso — independente das empresas."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("length(trim(name)) >= 2", name="name_min_length"),
        CheckConstraint("billing_cycle IN ('A_VISTA','SEMANAL','QUINZENAL','MENSAL')", name="billing_cycle"),
        CheckConstraint("document ~ '^([0-9]{11}|[0-9]{14})$'", name="document_digits"),
        Index("ix_customers_name_lower", func.lower(text("name"))),
        Index("uq_customers_document", "document", unique=True, postgresql_where=text("document IS NOT NULL")),
        Index("ix_customers_is_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    document: Mapped[str | None] = mapped_column(String(14))
    location: Mapped[str | None] = mapped_column(String(150))
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="MENSAL",
                                               server_default="MENSAL")
    start_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
