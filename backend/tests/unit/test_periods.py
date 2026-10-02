from datetime import date

import pytest

from app.core.errors import ValidationFailed
from app.services.periods import Period, ensure_series_limit, previous_period, resolve_period

TODAY = date(2026, 9, 30)  # quarta-feira


@pytest.mark.parametrize(("preset", "start", "end"), [
    ("today", date(2026, 9, 30), date(2026, 9, 30)),
    ("week", date(2026, 9, 28), date(2026, 9, 30)),  # FIN-02
    ("month", date(2026, 9, 1), date(2026, 9, 30)),
    ("last_month", date(2026, 8, 1), date(2026, 8, 31)),  # FIN-26
    (None, date(2026, 9, 1), date(2026, 9, 30)),  # padrão: mês
])
def test_presets(preset, start, end):
    p = resolve_period(preset, None, None, TODAY)
    assert (p.start_date, p.end_date) == (start, end)


def test_last_month_in_january():
    p = resolve_period("last_month", None, None, date(2027, 1, 15))
    assert (p.start_date, p.end_date) == (date(2026, 12, 1), date(2026, 12, 31))


def test_week_on_monday_and_sunday():
    assert resolve_period("week", None, None, date(2026, 9, 28)).start_date == date(2026, 9, 28)
    assert resolve_period("week", None, None, date(2026, 10, 4)).start_date == date(2026, 9, 28)


def test_custom_inclusive_days():  # R-PER-1
    p = resolve_period("custom", date(2026, 9, 1), date(2026, 9, 30), TODAY)
    assert p.days == 30
    assert list(p.iter_days())[0] == date(2026, 9, 1)
    assert list(p.iter_days())[-1] == date(2026, 9, 30)
    assert resolve_period("custom", TODAY, TODAY, TODAY).days == 1


def test_custom_requires_dates_and_order():  # DSH-01
    with pytest.raises(ValidationFailed):
        resolve_period("custom", None, TODAY, TODAY)
    with pytest.raises(ValidationFailed):
        resolve_period("custom", date(2026, 9, 2), date(2026, 9, 1), TODAY)
    with pytest.raises(ValueError):
        resolve_period("year", None, None, TODAY)


def test_previous_period():
    prev = previous_period(Period("month", date(2026, 9, 1), date(2026, 9, 30)))
    assert (prev.start_date, prev.end_date) == (date(2026, 8, 2), date(2026, 8, 31))
    assert prev.days == 30


def test_series_limit():
    ensure_series_limit(Period("custom", date(2025, 10, 1), date(2026, 9, 30)))  # 365 dias
    with pytest.raises(ValidationFailed):
        ensure_series_limit(Period("custom", date(2025, 1, 1), date(2026, 9, 30)))
