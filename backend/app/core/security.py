"""Hash de senha (Argon2id) e tokens JWT vinculados a sessão (ARCHITECTURE.md D-05)."""

import threading
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core import clock
from app.core.config import get_settings

_hasher = PasswordHasher()
# Usado para gastar o mesmo tempo quando o e-mail não existe (evita enumeração de usuários).
_DUMMY_HASH = _hasher.hash("senha-inexistente-para-tempo-constante")

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int, session_id: uuid.UUID, expires_at: datetime) -> str:
    settings = get_settings()
    payload = {"sub": str(user_id), "sid": str(session_id), "iat": int(clock.now().timestamp()),
               "exp": int(expires_at.timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                          options={"require": ["sub", "sid", "exp"], "verify_exp": False})
    except jwt.PyJWTError:
        return None


def token_expiration() -> datetime:
    return clock.now() + timedelta(minutes=get_settings().access_token_expire_minutes)


class LoginRateLimiter:
    """Limite de falhas de login por e-mail+IP, em memória (uso em 1–2 notebooks, ARCHITECTURE.md D-11)."""

    def __init__(self) -> None:
        self._failures: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _key(email: str, ip: str | None) -> str:
        return f"{email.strip().lower()}|{ip or '-'}"

    def _prune(self, key: str) -> deque[datetime]:
        window = timedelta(minutes=get_settings().login_failure_window_minutes)
        entries = self._failures[key]
        limit = clock.now() - window
        while entries and entries[0] < limit:
            entries.popleft()
        return entries

    def is_blocked(self, email: str, ip: str | None) -> bool:
        with self._lock:
            return len(self._prune(self._key(email, ip))) >= get_settings().login_max_failures

    def register_failure(self, email: str, ip: str | None) -> None:
        with self._lock:
            self._prune(self._key(email, ip)).append(clock.now())

    def reset(self, email: str | None = None, ip: str | None = None) -> None:
        with self._lock:
            if email is None:
                self._failures.clear()
            else:
                self._failures.pop(self._key(email, ip), None)


login_rate_limiter = LoginRateLimiter()
