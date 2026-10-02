"""Cenários financeiros obrigatórios no banco real (TEST-PLAN.md seção 2, parte (b)).

Dados de referência: FINANCIAL-RULES.md seção 7, inseridos pela API. Hoje = 30/09/2026.
"""

from datetime import UTC, date, datetime
from decimal import Decimal as D

import pytest

from app.core import clock
from app.core.errors import ValidationFailed
from app.services import financial_service as fs
from app.services.periods import resolve_period
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD
from tests.integration.helpers import build_reference, categories_by_name, make_cost, make_sale

TODAY = date(2026, 9, 30)


def period(preset="custom", start=None, end=None):
    return resolve_period(preset, start, end, TODAY)


@pytest.fixture
def ref(api):
    return build_reference(api)


def test_one_day(db, ref):  # FIN-01
    s = fs.summary(db, period(start=TODAY, end=TODAY))
    assert (s.revenue, s.quantity, s.total_costs, s.net_profit, s.average_cost_per_meal) == (
        D("185.00"), 10, D("33.33"), D("151.67"), D("3.33"))


def test_week(db, ref):  # FIN-02
    s = fs.summary(db, period("week"))
    assert (s.revenue, s.total_costs, s.net_profit) == (D("185.00"), D("33.33"), D("151.67"))


def test_month_everything_included(db, ref):  # FIN-03
    s = fs.summary(db, period("month"))
    assert s.revenue == D("1535.00")
    assert s.revenue_by_buyer_type == {"COMPANY": D("1425.00"), "CUSTOMER": D("110.00")}
    assert s.quantity == 80 and s.quantity_by_buyer_type == {"COMPANY": 75, "CUSTOMER": 5}
    assert (s.daily_costs, s.fixed_costs, s.total_costs) == (D("433.33"), D("300.00"), D("733.33"))
    assert s.net_profit == D("801.67")
    assert s.net_margin_percent == D("52.23")
    assert s.average_cost_per_meal == D("9.17")
    assert s.average_ticket == D("383.75")
    assert s.average_price_per_meal == D("19.19")


def test_custom_period(db, ref):  # FIN-04
    s = fs.summary(db, period(start=date(2026, 9, 1), end=date(2026, 9, 15)))
    assert (s.revenue, s.quantity, s.total_costs, s.net_profit, s.average_cost_per_meal) == (
        D("1240.00"), 65, D("700.00"), D("540.00"), D("10.77"))


def test_inclusive_borders(db, ref):  # FIN-05
    assert fs.summary(db, period(start=date(2026, 9, 1), end=date(2026, 9, 30))).revenue == D("1535.00")
    assert fs.summary(db, period(start=date(2026, 9, 2), end=date(2026, 9, 29))).revenue == D("610.00")


def test_company_revenue(db, ref):  # FIN-06
    detail = fs.buyer_detail(db, "COMPANY", ref.company_a["id"], period("month"))
    r = detail.revenue
    assert (r.revenue, r.quantity, r.sales_count) == (D("925.00"), 50, 2)
    assert (r.average_ticket, r.average_price_per_meal, r.revenue_share_percent) == (
        D("462.50"), D("18.50"), D("60.26"))
    assert not hasattr(r, "net_profit") and not hasattr(r, "allocated_costs")
    assert [s.sale_date for s in detail.recent_sales] == [date(2026, 9, 30), date(2026, 9, 1)]
    assert len(detail.daily) == 30
    assert detail.daily[0][1].revenue == D("740.00")


def test_revenue_by_buyer(db, ref):  # FIN-07
    b = fs.revenue_by_buyer(db, period("month"))
    assert b.revenue == D("1535.00")
    assert [(i.name, i.revenue, i.revenue_share_percent) for i in b.items] == [
        ("Empresa A", D("925.00"), D("60.26")),
        ("Empresa B", D("500.00"), D("32.57")),
        ("Cliente X", D("110.00"), D("7.17")),
    ]
    assert (b.subtotals["COMPANY"].revenue, b.subtotals["COMPANY"].quantity) == (D("1425.00"), 75)
    assert (b.subtotals["CUSTOMER"].revenue, b.subtotals["CUSTOMER"].quantity) == (D("110.00"), 5)
    assert sum((i.revenue for i in b.items), D(0)) == b.revenue


def test_no_sales(db, ref):  # FIN-08
    s = fs.summary(db, period(start=date(2026, 9, 5), end=date(2026, 9, 5)))
    assert (s.revenue, s.quantity, s.total_costs, s.net_profit) == (D("0.00"), 0, D("300.00"), D("-300.00"))
    assert s.average_cost_per_meal is None and s.average_ticket is None and s.net_margin_percent is None


def test_no_costs(db, ref):  # FIN-09
    s = fs.summary(db, period(start=date(2026, 9, 15), end=date(2026, 9, 15)))
    assert (s.revenue, s.total_costs, s.net_profit, s.average_cost_per_meal) == (
        D("500.00"), D("0.00"), D("500.00"), D("0.00"))


def test_no_sales_no_costs(db, ref):  # FIN-10
    p = period(start=date(2026, 9, 2), end=date(2026, 9, 4))
    s = fs.summary(db, p)
    assert (s.revenue, s.total_costs, s.net_profit) == (D("0.00"), D("0.00"), D("0.00"))
    assert s.average_cost_per_meal is None and s.average_ticket is None and s.net_margin_percent is None
    series = fs.daily(db, p)
    assert len(series) == 3 and all(d.revenue == D("0.00") and d.total_costs == D("0.00") for d in series)
    assert fs.revenue_by_buyer(db, p).items == []


def test_division_by_zero_everywhere(db, ref):  # FIN-11
    # 10–12/09 sem vendas; período anterior (07–09/09) também sem vendas.
    p = period(start=date(2026, 9, 10), end=date(2026, 9, 12))
    detail = fs.buyer_detail(db, "COMPANY", ref.company_a["id"], p)
    assert detail.revenue.average_ticket is None
    assert detail.revenue.average_price_per_meal is None
    assert detail.revenue.revenue_share_percent is None
    assert detail.revenue_change_percent is None


def test_only_fixed_costs(api, db):  # FIN-12
    b = api.ok(api.post("/companies", {"name": "Empresa B"}), 201)
    make_sale(api, b, "COMPANY", "20.00", 25, "2026-09-15")
    make_cost(api, categories_by_name(api)["Aluguel"], "300.00", "2026-09-05")
    s = fs.summary(db, period("month"))
    assert (s.fixed_costs, s.daily_costs, s.total_costs, s.average_cost_per_meal, s.net_profit) == (
        D("300.00"), D("0.00"), D("300.00"), D("12.00"), D("200.00"))


def test_only_daily_costs(api, db):  # FIN-13
    a = api.ok(api.post("/companies", {"name": "Empresa A"}), 201)
    make_sale(api, a, "COMPANY", "18.50", 40, "2026-09-01")
    make_cost(api, categories_by_name(api)["Ingredientes"], "400.00", "2026-09-01")
    s = fs.summary(db, period("month"))
    assert (s.daily_costs, s.fixed_costs, s.total_costs, s.average_cost_per_meal, s.net_profit) == (
        D("400.00"), D("0.00"), D("400.00"), D("10.00"), D("340.00"))


def test_sales_without_costs_longer_period(api, db):  # FIN-14
    a = api.ok(api.post("/companies", {"name": "Empresa A"}), 201)
    make_sale(api, a, "COMPANY", "18.50", 40, "2026-08-10")
    make_sale(api, a, "COMPANY", "18.50", 10, "2026-09-10")
    s = fs.summary(db, period(start=date(2026, 8, 1), end=date(2026, 9, 30)))
    assert s.net_profit == s.revenue == D("925.00")


def test_costs_without_sales_longer_period(api, db):  # FIN-15
    cats = categories_by_name(api)
    make_cost(api, cats["Aluguel"], "3000.00", "2026-08-05")
    make_cost(api, cats["Ingredientes"], "120.00", "2026-09-10")
    s = fs.summary(db, period(start=date(2026, 8, 1), end=date(2026, 9, 30)))
    assert s.net_profit == D("-3120.00") and s.average_cost_per_meal is None


def test_logical_deletion(api, db, ref):  # FIN-18
    api.delete(f"/sales/{ref.sales[0]['id']}")
    api.delete(f"/costs/{ref.costs[0]['id']}")
    s = fs.summary(db, period("month"))
    assert (s.revenue, s.quantity, s.total_costs) == (D("795.00"), 40, D("333.33"))
    items = fs.revenue_by_buyer(db, period("month")).items
    assert all(i.name != "Empresa A" or i.revenue == D("185.00") for i in items)


def test_daily_series_consistency(db, ref):  # FIN-19 / FIN-28
    p = period("month")
    series = fs.daily(db, p)
    s = fs.summary(db, p)
    assert len(series) == 30
    assert sum((d.revenue for d in series), D(0)) == s.revenue
    assert sum(d.quantity for d in series) == s.quantity
    assert sum((d.daily_costs for d in series), D(0)) == s.daily_costs
    assert sum((d.fixed_costs for d in series), D(0)) == s.fixed_costs
    assert series[-1].cumulative_costs == D("733.33")
    assert series[-1].cumulative_net_profit == D("801.67")
    assert series[4].net_profit == D("-300.00")


def test_series_limit(db, ref):  # DSH-01
    with pytest.raises(ValidationFailed):
        fs.daily(db, period(start=date(2025, 1, 1), end=TODAY))


def test_timezone_late_night_sale(api, client, db):  # FIN-20
    a = api.ok(api.post("/companies", {"name": "Empresa A"}), 201)
    # 23:30 de 30/09 em São Paulo = 02:30 UTC de 01/10.
    clock.set_now_provider(lambda: datetime(2026, 10, 1, 2, 30, tzinfo=UTC))
    login = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    api.headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    sale = make_sale(api, a, "COMPANY", "10.00", 1)
    assert sale["sale_date"] == "2026-09-30"
    future = api.post("/sales", {"buyer_type": "COMPANY", "company_id": a["id"], "unit_price": "1.00",
                                 "quantity": 1, "sale_date": "2026-10-01"})
    assert future.status_code == 422  # em São Paulo ainda é 30/09


def test_only_customers(api, db):  # FIN-24
    x = api.ok(api.post("/customers", {"name": "Cliente X"}), 201)
    make_sale(api, x, "CUSTOMER", "22.00", 5, "2026-09-20")
    b = fs.revenue_by_buyer(db, period("month"))
    assert b.subtotals["COMPANY"].revenue == D("0.00")
    assert b.revenue == b.subtotals["CUSTOMER"].revenue == D("110.00")


def test_retroactive_entries(api, db, ref):  # FIN-25
    make_sale(api, ref.company_b, "COMPANY", "20.00", 3, "2026-09-10")
    make_cost(api, ref.categories["Gasolina"], "45.00", "2026-09-10")
    day = fs.summary(db, period(start=date(2026, 9, 10), end=date(2026, 9, 10)))
    assert (day.revenue, day.total_costs) == (D("60.00"), D("45.00"))
    series = fs.daily(db, period("month"))
    assert series[9].revenue == D("60.00") and series[9].daily_costs == D("45.00")


def test_last_month(api, db, ref):  # FIN-26
    make_sale(api, ref.company_a, "COMPANY", "18.50", 20, "2026-08-31")
    p = period("last_month")
    assert (p.start_date, p.end_date) == (date(2026, 8, 1), date(2026, 8, 31))
    assert fs.summary(db, p).revenue == D("370.00")


def test_revenue_stable_across_filters(db, ref):  # FIN-27
    p = period("month")
    all_items = {i.buyer_id: i.revenue for i in fs.revenue_by_buyer(db, p).items if i.buyer_type == "COMPANY"}
    companies = {i.buyer_id: i.revenue for i in fs.revenue_by_buyer(db, p, buyer_type="COMPANY").items}
    detail = fs.buyer_detail(db, "COMPANY", ref.company_a["id"], p)
    assert all_items == companies
    assert companies[ref.company_a["id"]] == detail.revenue.revenue == D("925.00")
    customers = fs.revenue_by_buyer(db, p, buyer_type="CUSTOMER").items
    assert [(c.name, c.revenue_share_percent) for c in customers] == [("Cliente X", D("7.17"))]


def test_comparison_with_previous_period(api, db, ref):
    make_sale(api, ref.company_a, "COMPANY", "18.50", 50, "2026-08-15")  # 925.00 no período anterior
    detail = fs.buyer_detail(db, "COMPANY", ref.company_a["id"], period("month"))
    assert (detail.previous_period.start_date, detail.previous_period.end_date) == (date(2026, 8, 2),
                                                                                   date(2026, 8, 31))
    assert detail.previous.revenue == D("925.00")
    assert detail.revenue_change_percent == D("0.00")


def test_customer_detail(db, ref):
    detail = fs.buyer_detail(db, "CUSTOMER", ref.customer_x["id"], period("month"))
    assert (detail.revenue.revenue, detail.revenue.quantity, detail.revenue.average_price_per_meal) == (
        D("110.00"), 5, D("22.00"))


def test_inactive_company_keeps_history(api, db, ref):
    api.ok(api.post(f"/companies/{ref.company_a['id']}/deactivate", {"version": ref.company_a["version"]}))
    assert fs.buyer_detail(db, "COMPANY", ref.company_a["id"], period("month")).revenue.revenue == D("925.00")
    assert fs.summary(db, period("month")).revenue == D("1535.00")
