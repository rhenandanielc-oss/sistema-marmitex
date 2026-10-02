"""Utilitários comuns aos serviços: versão otimista, paginação, ordenação, integridade."""

from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.errors import Conflict, NotFound, ValidationFailed, VersionConflict

T = TypeVar("T")


def get_or_404(db: Session, model: type[T], entity_id: int, message: str = "Registro não encontrado.") -> T:
    obj = db.get(model, entity_id)
    if obj is None or getattr(obj, "deleted_at", None) is not None:
        raise NotFound(message)
    return obj


def check_version(entity: Any, version: int) -> None:
    if entity.version != version:
        raise VersionConflict()


def resolve_sort(sort: str | None, order: str, allowed: dict[str, Any], default: str) -> list[Any]:
    key = sort or default
    if key not in allowed:
        raise ValidationFailed(f"Ordenação inválida. Opções: {', '.join(sorted(allowed))}.", field="sort")
    column = allowed[key]
    return [column.desc() if order == "desc" else column.asc()]


def paginate(db: Session, stmt: Select[Any], order_by: list[Any], id_column: Any, page: int, page_size: int,
             transform: Callable[[Any], Any] | None = None) -> tuple[list[Any], int]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(
        stmt.order_by(*order_by, id_column.desc()).offset((page - 1) * page_size).limit(page_size)
    ).unique().all()
    items = [transform(r) for r in rows] if transform else list(rows)
    return items, total


def commit(db: Session, conflict_message: str = "Registro duplicado.") -> None:
    """Commit traduzindo violações de integridade e edição concorrente em erros de domínio."""
    try:
        db.commit()
    except StaleDataError as exc:
        db.rollback()
        raise VersionConflict() from exc
    except IntegrityError as exc:
        db.rollback()
        raise Conflict(conflict_message) from exc


def flush(db: Session, conflict_message: str = "Registro duplicado.") -> None:
    try:
        db.flush()
    except StaleDataError as exc:
        db.rollback()
        raise VersionConflict() from exc
    except IntegrityError as exc:
        db.rollback()
        raise Conflict(conflict_message) from exc
