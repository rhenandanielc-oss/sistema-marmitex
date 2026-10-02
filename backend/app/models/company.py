from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuthorMixin, Base, IdMixin, TimestampMixin, VersionMixin


class Company(IdMixin, TimestampMixin, VersionMixin, AuthorMixin, Base):
    """Empresa (empreiteira)."""

    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("length(trim(name)) >= 2", name="name_min_length"),
        CheckConstraint("billing_cycle IN ('QUINZENAL','MENSAL')", name="billing_cycle"),
        CheckConstraint("cnpj ~ '^[0-9]{14}$'", name="cnpj_digits"),
        Index("uq_companies_name_lower", func.lower(text("name")), unique=True),
        Index("uq_companies_cnpj", "cnpj", unique=True, postgresql_where=text("cnpj IS NOT NULL")),
        Index("ix_companies_is_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(150))
    cnpj: Mapped[str | None] = mapped_column(String(14))
    contact_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(254))
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="MENSAL",
                                               server_default="MENSAL")
    start_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
