from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Integer, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class VersionMixin:
    """Concorrência otimista (ARCHITECTURE.md D-08)."""

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    @declared_attr.directive
    def __mapper_args__(cls) -> dict:  # noqa: N805
        return {"version_id_col": cls.__table__.c.version}  # type: ignore[attr-defined]


class AuthorMixin:
    @declared_attr
    def created_by(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
