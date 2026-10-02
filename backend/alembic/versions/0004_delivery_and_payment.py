"""delivery type and payment status

Adds sales.delivery_type (RETIRADA/ENTREGA/OBRA), sales.payment_status (PAGO/PENDENTE)
and default_delivery_type on companies and customers.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-02
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DELIVERY = "IN ('RETIRADA','ENTREGA','OBRA')"


def upgrade() -> None:
    op.add_column("companies", sa.Column("default_delivery_type", sa.String(10), server_default="OBRA",
                                         nullable=False))
    op.create_check_constraint("ck_companies_default_delivery_type", "companies",
                               f"default_delivery_type {DELIVERY}")
    op.add_column("customers", sa.Column("default_delivery_type", sa.String(10), server_default="RETIRADA",
                                         nullable=False))
    op.create_check_constraint("ck_customers_default_delivery_type", "customers",
                               f"default_delivery_type {DELIVERY}")
    op.add_column("sales", sa.Column("delivery_type", sa.String(10), server_default="OBRA", nullable=False))
    op.add_column("sales", sa.Column("payment_status", sa.String(10), server_default="PENDENTE", nullable=False))
    # Vendas já existentes para clientes avulsos assumem o padrão "retirada".
    op.execute("UPDATE sales SET delivery_type = 'RETIRADA' WHERE buyer_type = 'CUSTOMER'")
    op.create_check_constraint("ck_sales_delivery_type", "sales", f"delivery_type {DELIVERY}")
    op.create_check_constraint("ck_sales_payment_status", "sales", "payment_status IN ('PAGO','PENDENTE')")
    op.create_index("ix_sales_payment_status_date", "sales", ["payment_status", "sale_date"],
                    postgresql_where=sa.text("deleted_at IS NULL"))


def downgrade() -> None:
    op.drop_index("ix_sales_payment_status_date", table_name="sales")
    op.drop_constraint("ck_sales_payment_status", "sales", type_="check")
    op.drop_constraint("ck_sales_delivery_type", "sales", type_="check")
    op.drop_column("sales", "payment_status")
    op.drop_column("sales", "delivery_type")
    op.drop_constraint("ck_customers_default_delivery_type", "customers", type_="check")
    op.drop_column("customers", "default_delivery_type")
    op.drop_constraint("ck_companies_default_delivery_type", "companies", type_="check")
    op.drop_column("companies", "default_delivery_type")
