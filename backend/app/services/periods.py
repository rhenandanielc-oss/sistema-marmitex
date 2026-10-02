"""Resolução de períodos (FINANCIAL-RULES.md seção 2). Intervalos sempre fechados [início, fim]."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from app.core.errors import ValidationFailed

MAX_SERIES_DAYS = 366


class PeriodPreset(StrEnum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    LAST_MONTH = "last_month"
    CUSTOM = "custom"


@dataclass(frozen=True)
class Period:
    preset: str
    start_date: date
    end_date: date

    @property
    def days(self) -> int:
        """Quantidade de dias, contando os dois extremos (R-PER-1)."""
        return (self.end_date - self.start_date).days + 1

    def iter_days(self) -> Iterator[date]:
        for offset in range(self.days):
            yield self.start_date + timedelta(days=offset)

    def contains(self, day: date) -> bool:
        return self.start_date <= day <= self.end_date


def resolve_period(preset: str | PeriodPreset | None, start_date: date | None, end_date: date | None,
                   today: date) -> Period:
    preset = PeriodPreset(preset or PeriodPreset.MONTH)
    if preset == PeriodPreset.TODAY:
        return Period(preset, today, today)
    if preset == PeriodPreset.WEEK:
        return Period(preset, today - timedelta(days=today.weekday()), today)
    if preset == PeriodPreset.MONTH:
        return Period(preset, today.replace(day=1), today)
    if preset == PeriodPreset.LAST_MONTH:
        last_day = today.replace(day=1) - timedelta(days=1)
        return Period(preset, last_day.replace(day=1), last_day)
    if start_date is None or end_date is None:
        details = [{"field": f, "message": "Obrigatório no período personalizado."}
                   for f, v in (("start_date", start_date), ("end_date", end_date)) if v is None]
        raise ValidationFailed("Informe a data inicial e a data final.", details=details)
    if start_date > end_date:
        raise ValidationFailed("A data inicial deve ser menor ou igual à data final.", field="start_date")
    return Period(preset, start_date, end_date)


def previous_period(period: Period) -> Period:
    """Período anterior de mesma duração, terminando na véspera do início (R-FAT-4)."""
    end = period.start_date - timedelta(days=1)
    return Period(PeriodPreset.CUSTOM, end - timedelta(days=period.days - 1), end)


def ensure_series_limit(period: Period, max_days: int = MAX_SERIES_DAYS) -> None:
    if period.days > max_days:
        raise ValidationFailed(f"Período máximo para séries diárias: {max_days} dias.", field="end_date")
