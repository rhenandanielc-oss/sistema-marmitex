"""Autenticação por requisição e autorização (papel único ADMIN — API.md seção 2)."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import clock
from app.core.db import get_db
from app.core.errors import Forbidden, Unauthenticated
from app.core.security import decode_access_token
from app.models import User, UserSession
from app.models.enums import Role

_bearer = HTTPBearer(auto_error=False, description="Token obtido em POST /auth/login")


class CurrentUser:
    def __init__(self, user: User, session: UserSession):
        self.user = user
        self.session = session

    @property
    def id(self) -> int:
        return self.user.id


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthenticated()
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise Unauthenticated("Sessão inválida. Faça login novamente.")
    try:
        session_id = uuid.UUID(payload["sid"])
        user_id = int(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise Unauthenticated("Sessão inválida. Faça login novamente.") from exc
    session = db.get(UserSession, session_id)
    now = clock.now()
    if session is None or session.user_id != user_id or session.revoked_at is not None or session.expires_at <= now:
        raise Unauthenticated("Sessão expirada. Faça login novamente.")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise Unauthenticated("Usuário inativo.")
    return CurrentUser(user, session)


def require_admin(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if current.user.role != Role.ADMIN:
        raise Forbidden()
    return current


AdminUser = Annotated[CurrentUser, Depends(require_admin)]
DbSession = Annotated[Session, Depends(get_db)]
