from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuthorMixin, Base, IdMixin, TimestampMixin, VersionMixin
from app.models.company import Company
from app.models.customer import Customer


class Sale(IdMixin, TimestampMixin, VersionMixin, AuthorMixin, Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("buyer_type IN ('COMPANY','CUSTOMER')", name="buyer_type"),
        CheckConstraint(
            "(buyer_type = 'COMPANY' AND company_id IS NOT NULL AND customer_id IS NULL) OR "
            "(buyer_type = 'CUSTOMER' AND customer_id IS NOT NULL AND company_id IS NULL)",
            name="single_buyer",
        ),
        CheckConstraint("unit_price > 0", name="unit_price_positive"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("subtotal = unit_price * quantity", name="subtotal_formula"),
        Index("ix_sales_sale_date", "sale_date", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_sales_company_date", "company_id", "sale_date",
              postgresql_where=text("deleted_at IS NULL AND company_id IS NOT NULL")),
        Index("ix_sales_customer_date", "customer_id", "sale_date",
              postgresql_where=text("deleted_at IS NULL AND customer_id IS NOT NULL")),
        Index("ix_sales_buyer_type_date", "buyer_type", "sale_date", postgresql_where=text("deleted_at IS NULL")),
    )

    buyer_type: Mapped[str] = mapped_column(String(10), nullable=False)
    company_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("companies.id", ondelete="RESTRICT"))
    customer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"))
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    company: Mapped[Company | None] = relationship(lazy="joined")
    customer: Mapped[Customer | None] = relationship(lazy="joined")
