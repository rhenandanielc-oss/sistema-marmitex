from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict
from app.core.permissions import CurrentUser
from app.core.security import hash_password
from app.models import User
from app.models.enums import AuditAction, Role
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit
from app.services.auth_service import find_user_by_email, revoke_user_sessions
from app.services.common import check_version, commit, flush, get_or_404, paginate, resolve_sort

SORTS = {"name": func.lower(User.name), "email": func.lower(User.email), "created_at": User.created_at}
NOT_FOUND = "Usuário não encontrado."
DUPLICATE_EMAIL = "Já existe um usuário com este e-mail."


def list_users(db: Session, *, q: str | None, active: bool | None, sort: str | None, order: str,
               page: int, page_size: int) -> tuple[list[User], int]:
    stmt = select(User)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.name.ilike(like), User.email.ilike(like)))
    if active is not None:
        stmt = stmt.where(User.is_active.is_(active))
    return paginate(db, stmt, resolve_sort(sort, order, SORTS, "name"), User.id, page, page_size)


def create_user(db: Session, data: UserCreate, actor: CurrentUser) -> User:
    if find_user_by_email(db, data.email):
        raise Conflict(DUPLICATE_EMAIL)
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password),
                role=Role.ADMIN)
    db.add(user)
    flush(db, DUPLICATE_EMAIL)
    audit.record(db, action=AuditAction.CREATE, entity_type="user", entity_id=user.id, user_id=actor.id,
                 after=audit.snapshot(user))
    commit(db, DUPLICATE_EMAIL)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, actor: CurrentUser) -> User:
    user = get_or_404(db, User, user_id, NOT_FOUND)
    check_version(user, data.version)
    before = audit.snapshot(user)
    if data.email is not None and data.email.lower() != user.email.lower():
        existing = find_user_by_email(db, data.email)
        if existing and existing.id != user.id:
            raise Conflict(DUPLICATE_EMAIL)
        user.email = data.email.lower()
    if data.name is not None:
        user.name = data.name
    flush(db, DUPLICATE_EMAIL)
    audit.record(db, action=AuditAction.UPDATE, entity_type="user", entity_id=user.id, user_id=actor.id,
                 before=before, after=audit.snapshot(user))
    commit(db, DUPLICATE_EMAIL)
    return user


def set_user_active(db: Session, user_id: int, active: bool, actor: CurrentUser) -> User:
    user = get_or_404(db, User, user_id, NOT_FOUND)
    if user.is_active == active:
        return user
    if not active:
        if user.id == actor.id:
            raise Conflict("Você não pode desativar o próprio usuário.")
        active_admins = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
        if active_admins <= 1:
            raise Conflict("Não é possível desativar o último administrador ativo.")
    before = audit.snapshot(user)
    user.is_active = active
    if not active:
        revoke_user_sessions(db, user.id)
    flush(db)
    audit.record(db, action=AuditAction.ACTIVATE if active else AuditAction.DEACTIVATE, entity_type="user",
                 entity_id=user.id, user_id=actor.id, before=before, after=audit.snapshot(user))
    commit(db)
    return user


def reset_password(db: Session, user_id: int, new_password: str, actor: CurrentUser) -> None:
    user = get_or_404(db, User, user_id, NOT_FOUND)
    user.password_hash = hash_password(new_password)
    revoke_user_sessions(db, user.id, except_session_id=actor.session.id if user.id == actor.id else None)
    audit.record(db, action=AuditAction.PASSWORD_CHANGE, entity_type="user", entity_id=user.id,
                 user_id=actor.id)
    commit(db)
