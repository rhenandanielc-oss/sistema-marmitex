"""Gravação de auditoria na mesma transação da operação (ARCHITECTURE.md princípio 4)."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.request_context import get_request_info
from app.models import AuditLog

# Campos que nunca podem aparecer na auditoria.
_SENSITIVE = {"password_hash", "password"}
_SKIP = {"created_at", "updated_at"}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def snapshot(entity: Any) -> dict[str, Any]:
    """Estado das colunas de uma entidade, sem campos sensíveis."""
    mapper = inspect(entity).mapper
    return {
        col.key: _jsonable(getattr(entity, col.key))
        for col in mapper.column_attrs
        if col.key not in _SENSITIVE and col.key not in _SKIP
    }


def record(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Any = None,
    user_id: int | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditLog:
    info = get_request_info()
    if before is not None and after is not None:
        changed = {k for k in after if before.get(k) != after.get(k)} | {"id", "version"}
        before = {k: v for k, v in before.items() if k in changed}
        after = {k: v for k, v in after.items() if k in changed}
    log = AuditLog(
        action=str(action),
        entity_type=entity_type,
        entity_id=None if entity_id is None else str(entity_id),
        user_id=user_id,
        before_data=before,
        after_data=after,
        ip_address=info.ip_address,
        user_agent=(info.user_agent or "")[:255] or None,
        request_id=info.request_id,
    )
    db.add(log)
    return log
