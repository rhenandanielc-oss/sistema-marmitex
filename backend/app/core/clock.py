"""Relógio do negócio.

Todo acesso a "agora" e "hoje" passa por aqui, para que os testes possam fixar o tempo.
"Hoje" é a data atual no fuso APP_TIMEZONE (FINANCIAL-RULES.md R-PER-3).
"""

from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def _system_now() -> datetime:
    return datetime.now(UTC)


_now_provider: Callable[[], datetime] = _system_now


def now() -> datetime:
    """Instante atual (timezone-aware, UTC)."""
    return _now_provider()


def today() -> date:
    """Data de hoje no fuso do negócio."""
    return now().astimezone(ZoneInfo(get_settings().app_timezone)).date()


def set_now_provider(provider: Callable[[], datetime]) -> None:
    global _now_provider
    _now_provider = provider


def reset() -> None:
    set_now_provider(_system_now)
