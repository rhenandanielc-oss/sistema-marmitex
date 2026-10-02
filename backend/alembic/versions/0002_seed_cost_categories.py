"""seed cost categories

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIES = [
    ("Ingredientes", "CUSTO_DIARIO"),
    ("Embalagens", "CUSTO_DIARIO"),
    ("Entregas", "CUSTO_DIARIO"),
    ("Equipamentos", "CUSTO_DIARIO"),
    ("Gasolina", "CUSTO_DIARIO"),
    ("Salários", "CUSTO_FIXO"),
    ("Aluguel", "CUSTO_FIXO"),
    ("Água", "CUSTO_FIXO"),
    ("Energia elétrica", "CUSTO_FIXO"),
    ("Gás", "CUSTO_FIXO"),
]


def upgrade() -> None:
    table = sa.table("cost_categories", sa.column("name", sa.String), sa.column("cost_type", sa.String))
    op.bulk_insert(table, [{"name": n, "cost_type": t} for n, t in CATEGORIES])


def downgrade() -> None:
    names = ", ".join(f"'{n}'" for n, _ in CATEGORIES)
    op.execute(
        f"DELETE FROM cost_categories WHERE name IN ({names}) "
        "AND NOT EXISTS (SELECT 1 FROM costs WHERE costs.category_id = cost_categories.id)"
    )
