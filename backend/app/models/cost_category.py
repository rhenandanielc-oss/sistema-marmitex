from sqlalchemy import Boolean, CheckConstraint, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuthorMixin, Base, IdMixin, TimestampMixin, VersionMixin


class CostCategory(IdMixin, TimestampMixin, VersionMixin, AuthorMixin, Base):
    __tablename__ = "cost_categories"
    __table_args__ = (
        CheckConstraint("cost_type IN ('CUSTO_DIARIO','CUSTO_FIXO')", name="cost_type"),
        CheckConstraint("length(trim(name)) >= 2", name="name_min_length"),
        UniqueConstraint("id", "cost_type", name="uq_cost_categories_id_cost_type"),
        Index("uq_cost_categories_name_lower", func.lower(text("name")), unique=True),
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
