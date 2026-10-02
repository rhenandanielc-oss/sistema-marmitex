"""Contexto da requisição (request_id, IP, user agent) para logs e auditoria."""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestInfo:
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


_current: ContextVar[RequestInfo] = ContextVar("request_info", default=RequestInfo())  # noqa: B039 (imutável)


def set_request_info(info: RequestInfo) -> None:
    _current.set(info)


def get_request_info() -> RequestInfo:
    return _current.get()


def get_request_id() -> str | None:
    return _current.get().request_id
