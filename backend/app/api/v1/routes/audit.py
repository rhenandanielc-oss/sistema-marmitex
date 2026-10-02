from datetime import date, datetime, time, timedelta
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.config import get_settings
from app.core.permissions import AdminUser, DbSession
from app.models import AuditLog
from app.schemas.common import OutputModel, Page, SortOrder
from app.services.common import paginate, resolve_sort

router = APIRouter(prefix="/audit-logs", tags=["Auditoria"])


class AuditLogRead(OutputModel):
    id: int
    occurred_at: datetime
    user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    ip_address: str | None
    request_id: str | None


@router.get("", response_model=Page[AuditLogRead], summary="Consulta a auditoria")
def list_audit_logs(
    admin: AdminUser, db: DbSession,
    user_id: int | None = None, entity_type: str | None = None, entity_id: str | None = None,
    action: str | None = None, start_date: date | None = None, end_date: date | None = None,
    order: SortOrder = "desc",
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[AuditLogRead]:
    tz = ZoneInfo(get_settings().app_timezone)
    stmt = select(AuditLog)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if start_date:
        stmt = stmt.where(AuditLog.occurred_at >= datetime.combine(start_date, time.min, tz))
    if end_date:
        stmt = stmt.where(AuditLog.occurred_at < datetime.combine(end_date + timedelta(days=1), time.min, tz))
    items, total = paginate(db, stmt, resolve_sort(None, order, {"occurred_at": AuditLog.occurred_at},
                                                   "occurred_at"), AuditLog.id, page, page_size)
    return Page.build([AuditLogRead.model_validate(i) for i in items], total, page, page_size)
