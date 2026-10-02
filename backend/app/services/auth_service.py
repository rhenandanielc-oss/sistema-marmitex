from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import InvalidCredentials, TooManyRequests, ValidationFailed
from app.core.permissions import CurrentUser
from app.core.request_context import get_request_info
from app.core.security import (
    create_access_token,
    hash_password,
    login_rate_limiter,
    token_expiration,
    verify_password,
)
from app.models import User, UserSession
from app.models.enums import AuditAction
from app.services import audit


@dataclass
class LoginResult:
    access_token: str
    expires_at: datetime
    user: User


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))


def login(db: Session, email: str, password: str) -> LoginResult:
    info = get_request_info()
    if login_rate_limiter.is_blocked(email, info.ip_address):
        raise TooManyRequests()
    user = find_user_by_email(db, email)
    password_ok = verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok or not user.is_active:
        login_rate_limiter.register_failure(email, info.ip_address)
        audit.record(db, action=AuditAction.LOGIN_FAILED, entity_type="session",
                     user_id=user.id if user else None, after={"email": email.strip().lower()})
        db.commit()
        raise InvalidCredentials()

    expires_at = token_expiration()
    session = UserSession(user_id=user.id, expires_at=expires_at, ip_address=info.ip_address,
                          user_agent=(info.user_agent or "")[:255] or None)
    db.add(session)
    user.last_login_at = clock.now()
    db.flush()
    audit.record(db, action=AuditAction.LOGIN_SUCCESS, entity_type="session", entity_id=session.id,
                 user_id=user.id)
    db.commit()
    login_rate_limiter.reset(email, info.ip_address)
    return LoginResult(create_access_token(user.id, session.id, expires_at), expires_at, user)


def logout(db: Session, current: CurrentUser) -> None:
    current.session.revoked_at = clock.now()
    audit.record(db, action=AuditAction.LOGOUT, entity_type="session", entity_id=current.session.id,
                 user_id=current.id)
    db.commit()


def revoke_user_sessions(db: Session, user_id: int, except_session_id: object | None = None) -> None:
    stmt = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    if except_session_id is not None:
        stmt = stmt.where(UserSession.id != except_session_id)
    db.execute(stmt.values(revoked_at=clock.now()))


def change_password(db: Session, current: CurrentUser, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, current.user.password_hash):
        raise ValidationFailed("Senha atual incorreta.", field="current_password")
    current.user.password_hash = hash_password(new_password)
    revoke_user_sessions(db, current.id, except_session_id=current.session.id)
    audit.record(db, action=AuditAction.PASSWORD_CHANGE, entity_type="user", entity_id=current.id,
                 user_id=current.id)
    db.commit()
