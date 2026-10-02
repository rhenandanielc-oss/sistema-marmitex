"""Testes unitários do motor financeiro (TEST-PLAN.md seção 2, parte (a))."""

from datetime import date, timedelta
from decimal import Decimal as D

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services import financial_engine as fe

COMPANY, CUSTOMER = fe.BUYER_COMPANY, fe.BUYER_CUSTOMER


def S(revenue: str, quantity: int, count: int) -> fe.SalesTotals:  # noqa: N802
    return fe.SalesTotals(D(revenue), quantity, count)


# Dados de referência — FINANCIAL-RULES.md seção 7 (setembro/2026).
REF_SALES = {COMPANY: S("1425.00", 75, 3), CUSTOMER: S("110.00", 5, 1)}
REF_COSTS = fe.CostTotals(daily=D("433.33"), fixed=D("300.00"), count=3)


def test_reference_month_summary():  # FIN-03
    s = fe.summarize(REF_SALES, REF_COSTS)
    assert s.revenue == D("1535.00")
    assert s.revenue_by_buyer_type == {COMPANY: D("1425.00"), CUSTOMER: D("110.00")}
    assert s.quantity == 80
    assert s.quantity_by_buyer_type == {COMPANY: 75, CUSTOMER: 5}
    assert s.sales_count == 4
    assert s.daily_costs == D("433.33")
    assert s.fixed_costs == D("300.00")
    assert s.total_costs == D("733.33")
    assert s.net_profit == D("801.67")
    assert s.net_margin_percent == D("52.23")
    assert s.average_cost_per_meal == D("9.17")
    assert s.average_ticket == D("383.75")
    assert s.average_price_per_meal == D("19.19")


def test_no_sales_no_costs():  # FIN-10
    s = fe.summarize({}, fe.CostTotals())
    assert (s.revenue, s.total_costs, s.net_profit, s.quantity) == (D("0.00"), D("0.00"), D("0.00"), 0)
    assert s.average_cost_per_meal is None
    assert s.average_ticket is None
    assert s.average_price_per_meal is None
    assert s.net_margin_percent is None


def test_costs_without_sales():  # FIN-08 / FIN-15
    s = fe.summarize({}, fe.CostTotals(fixed=D("300.00")))
    assert s.net_profit == D("-300.00")
    assert s.average_cost_per_meal is None
    assert s.net_margin_percent is None


def test_sales_without_costs():  # FIN-09 / FIN-14
    s = fe.summarize({COMPANY: S("500.00", 25, 1)}, fe.CostTotals())
    assert s.net_profit == D("500.00")
    assert s.average_cost_per_meal == D("0.00")
    assert s.net_margin_percent == D("100.00")


def test_only_fixed_costs():  # FIN-12
    s = fe.summarize({COMPANY: S("500.00", 25, 1)}, fe.CostTotals(fixed=D("300.00")))
    assert (s.fixed_costs, s.daily_costs, s.total_costs) == (D("300.00"), D("0.00"), D("300.00"))
    assert s.average_cost_per_meal == D("12.00")
    assert s.net_profit == D("200.00")


def test_only_daily_costs():  # FIN-13
    s = fe.summarize({COMPANY: S("740.00", 40, 1)}, fe.CostTotals(daily=D("400.00")))
    assert (s.daily_costs, s.fixed_costs, s.total_costs) == (D("400.00"), D("0.00"), D("400.00"))
    assert s.average_cost_per_meal == D("10.00")
    assert s.net_profit == D("340.00")


def test_negative_profit_exact():  # FIN-21
    s = fe.summarize({COMPANY: S("10.01", 1, 1)}, fe.CostTotals(daily=D("100.00"), fixed=D("0.02")))
    assert s.net_profit == D("-90.01")


@pytest.mark.parametrize(("total", "qty", "expected"), [
    ("10.00", 3, "3.33"), ("10.00", 6, "1.67"), ("0.05", 2, "0.03"), ("733.33", 80, "9.17"), ("33.33", 10, "3.33"),
])
def test_rounding_half_up(total, qty, expected):  # FIN-16
    s = fe.summarize({COMPANY: S("1.00", qty, 1)}, fe.CostTotals(daily=D(total)))
    assert s.average_cost_per_meal == D(expected)


@pytest.mark.parametrize(("price", "qty", "expected"), [
    ("18.50", 40, "740.00"), ("0.01", 10000, "100.00"), ("9999.99", 10000, "99999900.00"), ("22.00", 5, "110.00"),
])
def test_subtotal_exact(price, qty, expected):  # FIN-17
    assert fe.sale_subtotal(D(price), qty) == D(expected)


@pytest.mark.parametrize(("price", "qty"), [("0", 1), ("-1.00", 1), ("10.00", 0), ("1.005", 1)])
def test_subtotal_rejects_invalid(price, qty):
    with pytest.raises(ValueError):
        fe.sale_subtotal(D(price), qty)


def test_precision_many_small_sales():  # FIN-22
    total = sum((fe.sale_subtotal(D("0.01"), 1) for _ in range(1000)), fe.ZERO)
    assert total == D("10.00")


def test_revenue_breakdown_reference():  # FIN-07
    buyers = [
        fe.BuyerTotals(COMPANY, 1, "Empresa A", S("925.00", 50, 2)),
        fe.BuyerTotals(COMPANY, 2, "Empresa B", S("500.00", 25, 1)),
        fe.BuyerTotals(CUSTOMER, 1, "Cliente X", S("110.00", 5, 1)),
    ]
    b = fe.revenue_breakdown(buyers)
    assert b.revenue == D("1535.00")
    a, bb, x = b.items
    assert (a.revenue, a.average_ticket, a.average_price_per_meal, a.revenue_share_percent) == (
        D("925.00"), D("462.50"), D("18.50"), D("60.26"))
    assert (bb.revenue_share_percent, x.revenue_share_percent) == (D("32.57"), D("7.17"))
    assert x.average_price_per_meal == D("22.00")
    assert b.subtotals[COMPANY] == S("1425.00", 75, 3)
    assert b.subtotals[CUSTOMER] == S("110.00", 5, 1)
    assert not hasattr(a, "net_profit")  # R-FAT-1: sem lucro por comprador


def test_revenue_breakdown_zero_total():  # FIN-11
    b = fe.revenue_breakdown([fe.BuyerTotals(COMPANY, 1, "A", fe.SalesTotals())])
    assert b.items[0].revenue_share_percent is None
    assert b.items[0].average_ticket is None


def test_percent_change():
    assert fe.percent_change(D("112.50"), D("100.00")) == D("12.50")
    assert fe.percent_change(D("50.00"), D("100.00")) == D("-50.00")
    assert fe.percent_change(D("10.00"), D("0.00")) is None  # FIN-11


def test_running_totals():  # FIN-23
    assert fe.running_totals([D("400.00"), D("300.00"), D("33.33")]) == [D("400.00"), D("700.00"), D("733.33")]
    assert fe.running_totals([]) == []


def test_daily_series_reference():  # FIN-19 / FIN-28
    start = date(2026, 9, 1)
    days = [start + timedelta(days=i) for i in range(30)]
    sales = {date(2026, 9, 1): S("740.00", 40, 1), date(2026, 9, 15): S("500.00", 25, 1),
             date(2026, 9, 20): S("110.00", 5, 1), date(2026, 9, 30): S("185.00", 10, 1)}
    costs = {date(2026, 9, 1): fe.CostTotals(daily=D("400.00"), count=1),
             date(2026, 9, 5): fe.CostTotals(fixed=D("300.00"), count=1),
             date(2026, 9, 30): fe.CostTotals(daily=D("33.33"), count=1)}
    series = fe.daily_series(days, sales, costs)
    assert len(series) == 30
    first = series[0]
    assert (first.revenue, first.total_costs, first.net_profit, first.average_cost_per_meal) == (
        D("740.00"), D("400.00"), D("340.00"), D("10.00"))
    assert series[1].revenue == D("0.00") and series[1].average_cost_per_meal is None
    assert series[4].net_profit == D("-300.00")  # dia do aluguel: negativo é esperado (R-CUS-5)
    assert series[-1].cumulative_costs == D("733.33")
    assert series[-1].cumulative_net_profit == D("801.67")
    assert series[-1].cumulative_revenue == D("1535.00")
    assert sum((d.revenue for d in series), fe.ZERO) == D("1535.00")


money = st.decimals(min_value=D("0.01"), max_value=D("9999.99"), places=2, allow_nan=False, allow_infinity=False)


@settings(max_examples=200, deadline=None)
@given(
    sales=st.lists(st.tuples(st.sampled_from([COMPANY, CUSTOMER]), st.integers(1, 30), money,
                             st.integers(1, 200)), max_size=40),
    costs=st.lists(st.tuples(st.booleans(), st.integers(1, 30), money), max_size=40),
)
def test_properties(sales, costs):  # teste de propriedade (TEST-PLAN.md seção 2)
    start = date(2026, 9, 1)
    days = [start + timedelta(days=i) for i in range(30)]
    by_type: dict[str, fe.SalesTotals] = {}
    by_day: dict[date, fe.SalesTotals] = {}
    buyers: dict[tuple[str, int], fe.SalesTotals] = {}
    for btype, day, price, qty in sales:
        t = fe.SalesTotals(fe.sale_subtotal(price, qty), qty, 1)
        d = days[day - 1]
        by_type[btype] = by_type.get(btype, fe.SalesTotals()) + t
        by_day[d] = by_day.get(d, fe.SalesTotals()) + t
        key = (btype, day % 5)
        buyers[key] = buyers.get(key, fe.SalesTotals()) + t
    cost_total = fe.CostTotals()
    cost_by_day: dict[date, fe.CostTotals] = {}
    for is_fixed, day, amount in costs:
        c = fe.CostTotals(fixed=amount, count=1) if is_fixed else fe.CostTotals(daily=amount, count=1)
        cost_total = cost_total + c
        d = days[day - 1]
        cost_by_day[d] = cost_by_day.get(d, fe.CostTotals()) + c

    s = fe.summarize(by_type, cost_total)
    assert s.total_costs == s.fixed_costs + s.daily_costs
    assert s.net_profit == s.revenue - s.total_costs
    series = fe.daily_series(days, by_day, cost_by_day)
    assert sum((d.revenue for d in series), fe.ZERO) == s.revenue
    assert sum(d.quantity for d in series) == s.quantity
    assert sum((d.daily_costs for d in series), fe.ZERO) == s.daily_costs
    assert sum((d.fixed_costs for d in series), fe.ZERO) == s.fixed_costs
    assert series[-1].cumulative_costs == s.total_costs
    assert series[-1].cumulative_net_profit == s.net_profit
    assert series[-1].cumulative_revenue == s.revenue
    breakdown = fe.revenue_breakdown([fe.BuyerTotals(k[0], k[1], str(k), v) for k, v in buyers.items()])
    assert breakdown.revenue == s.revenue
    assert sum((i.revenue for i in breakdown.items), fe.ZERO) == s.revenue
