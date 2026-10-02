"""Histórico e dashboard via HTTP (TEST-PLAN.md seção 7: HIS-*, DSH-*). Hoje = 30/09/2026."""

import pytest

from tests.integration.helpers import build_reference, make_cost, make_sale

MONTH = {"start_date": "2026-09-01", "end_date": "2026-09-30", "days": 30}


@pytest.fixture
def ref(api):
    return build_reference(api)


# ---------- Dashboard ----------

def test_summary_matches_api_doc(api, ref):
    body = api.ok(api.get("/dashboard/summary"))
    assert body == {
        "period": {"preset": "month", **MONTH},
        "revenue": "1535.00",
        "revenue_by_buyer_type": {"COMPANY": "1425.00", "CUSTOMER": "110.00"},
        "quantity": 80,
        "quantity_by_buyer_type": {"COMPANY": 75, "CUSTOMER": 5},
        "sales_count": 4,
        "daily_costs": "433.33",
        "fixed_costs": "300.00",
        "total_costs": "733.33",
        "net_profit": "801.67",
        "net_margin_percent": "52.23",
        "average_cost_per_meal": "9.17",
        "average_ticket": "383.75",
        "average_price_per_meal": "19.19",
        "pending_revenue": "1535.00",
    }


@pytest.mark.parametrize(("params", "expected"), [
    ({"period": "today"}, ("2026-09-30", "2026-09-30", "185.00", "151.67")),
    ({"period": "week"}, ("2026-09-28", "2026-09-30", "185.00", "151.67")),
    ({"period": "last_month"}, ("2026-08-01", "2026-08-31", "0.00", "0.00")),
    ({"period": "custom", "start_date": "2026-09-05", "end_date": "2026-09-05"},
     ("2026-09-05", "2026-09-05", "0.00", "-300.00")),
])
def test_summary_periods(api, ref, params, expected):
    body = api.ok(api.get("/dashboard/summary", params=params))
    assert (body["period"]["start_date"], body["period"]["end_date"], body["revenue"], body["net_profit"]) == expected


def test_summary_empty_period_nulls(api, ref):  # FIN-10 / FIN-11
    body = api.ok(api.get("/dashboard/summary", params={"period": "custom", "start_date": "2026-09-02",
                                                        "end_date": "2026-09-04"}))
    assert body["revenue"] == "0.00" and body["net_profit"] == "0.00"
    assert body["average_cost_per_meal"] is None
    assert body["average_ticket"] is None
    assert body["net_margin_percent"] is None


@pytest.mark.parametrize("params", [
    {"period": "ano"},
    {"period": "custom"},
    {"period": "custom", "start_date": "2026-09-10"},
    {"period": "custom", "start_date": "2026-09-10", "end_date": "2026-09-01"},
    {"period": "custom", "start_date": "10/09/2026", "end_date": "2026-09-30"},
])
def test_invalid_periods(api, params):  # DSH-01
    resp = api.get("/dashboard/summary", params=params)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_daily_series_limit(api):  # DSH-01
    resp = api.get("/dashboard/daily", params={"period": "custom", "start_date": "2025-01-01",
                                               "end_date": "2026-09-30"})
    assert resp.status_code == 422


def test_daily(api, ref):  # FIN-19 / FIN-28
    body = api.ok(api.get("/dashboard/daily"))
    items = body["items"]
    assert len(items) == 30
    assert items[0] == {"date": "2026-09-01", "revenue": "740.00", "cumulative_revenue": "740.00",
                        "quantity": 40, "sales_count": 1,
                        "daily_costs": "400.00", "fixed_costs": "0.00", "total_costs": "400.00",
                        "cumulative_costs": "400.00", "net_profit": "340.00", "cumulative_net_profit": "340.00",
                        "average_cost_per_meal": "10.00"}
    assert items[1]["revenue"] == "0.00" and items[1]["average_cost_per_meal"] is None
    assert items[4]["net_profit"] == "-300.00"
    assert items[-1]["cumulative_revenue"] == "1535.00"
    assert items[-1]["cumulative_costs"] == "733.33"
    assert items[-1]["cumulative_net_profit"] == "801.67"


def test_by_buyer(api, ref):  # DSH-03 / FIN-07
    body = api.ok(api.get("/dashboard/by-buyer"))
    assert body["revenue"] == "1535.00"
    assert [(i["buyer"]["name"], i["buyer"]["type"], i["revenue"], i["revenue_share_percent"])
            for i in body["items"]] == [
        ("Empresa A", "COMPANY", "925.00", "60.26"),
        ("Empresa B", "COMPANY", "500.00", "32.57"),
        ("Cliente X", "CUSTOMER", "110.00", "7.17"),
    ]
    a = body["items"][0]
    assert (a["quantity"], a["sales_count"], a["average_ticket"], a["average_price_per_meal"]) == (
        50, 2, "462.50", "18.50")
    assert "net_profit" not in a and "allocated_costs" not in a  # R-FAT-1
    assert body["subtotals"] == {"COMPANY": {"revenue": "1425.00", "quantity": 75, "sales_count": 3},
                                 "CUSTOMER": {"revenue": "110.00", "quantity": 5, "sales_count": 1}}
    shares = sum(float(i["revenue_share_percent"]) for i in body["items"])
    assert abs(shares - 100) < 0.05


def test_by_buyer_filters_and_sort(api, ref):  # FIN-27
    companies = api.ok(api.get("/dashboard/by-buyer", params={"buyer_type": "COMPANY"}))
    assert [i["buyer"]["name"] for i in companies["items"]] == ["Empresa A", "Empresa B"]
    assert companies["items"][0]["revenue_share_percent"] == "60.26"  # sempre sobre a receita total
    customers = api.ok(api.get("/dashboard/by-buyer", params={"buyer_type": "CUSTOMER"}))
    assert [i["buyer"]["name"] for i in customers["items"]] == ["Cliente X"]
    by_qty = api.ok(api.get("/dashboard/by-buyer", params={"sort": "quantity", "order": "asc"}))
    assert [i["quantity"] for i in by_qty["items"]] == [5, 25, 50]
    by_name = api.ok(api.get("/dashboard/by-buyer", params={"sort": "name", "order": "asc"}))
    assert [i["buyer"]["name"] for i in by_name["items"]] == ["Cliente X", "Empresa A", "Empresa B"]
    assert api.get("/dashboard/by-buyer", params={"sort": "lucro"}).status_code == 422


def test_sales_by_company_daily(api, ref):
    body = api.ok(api.get("/dashboard/sales-by-company-daily"))
    a, b = ref.company_a["id"], ref.company_b["id"]
    assert body["companies"] == [{"id": a, "name": "Empresa A"}, {"id": b, "name": "Empresa B"}]
    assert body["has_other_companies"] is False
    days = {i["date"]: i for i in body["items"]}
    assert len(days) == 30
    assert days["2026-09-01"]["values"] == {str(a): "740.00", str(b): "0.00"}
    assert days["2026-09-15"]["values"][str(b)] == "500.00"
    assert days["2026-09-20"]["customers"] == "110.00"
    assert days["2026-09-20"]["other_companies"] == "0.00"


def test_sales_by_company_daily_top_10(api):
    companies = [api.ok(api.post("/companies", {"name": f"Empresa {i:02d}"}), 201) for i in range(12)]
    for i, c in enumerate(companies):
        make_sale(api, c, "COMPANY", "10.00", i + 1, "2026-09-10")
    body = api.ok(api.get("/dashboard/sales-by-company-daily"))
    assert len(body["companies"]) == 10 and body["has_other_companies"] is True
    day = next(i for i in body["items"] if i["date"] == "2026-09-10")
    assert day["other_companies"] == "30.00"  # as duas menores: 1 + 2 marmitas × 10,00
    assert sum(float(v) for v in day["values"].values()) + float(day["other_companies"]) == 780.0
    top6 = api.ok(api.get("/dashboard/sales-by-company-daily", params={"top": 6}))
    assert len(top6["companies"]) == 6
    day6 = next(i for i in top6["items"] if i["date"] == "2026-09-10")
    assert day6["other_companies"] == "210.00"  # 1+2+...+6 marmitas × 10,00
    assert api.get("/dashboard/sales-by-company-daily", params={"top": 11}).status_code == 422


def test_company_dashboard(api, ref):  # DSH-02
    api.ok(api.patch(f"/companies/{ref.company_a['id']}", {"start_date": "2026-03-01", "payment_date": "2026-10-05",
                                                         "version": ref.company_a["version"]}))
    make_sale(api, ref.company_a, "COMPANY", "18.50", 20, "2026-08-20")
    body = api.ok(api.get(f"/dashboard/companies/{ref.company_a['id']}"))
    assert body["buyer"] == {"type": "COMPANY", "id": ref.company_a["id"], "name": "Empresa A", "is_active": True,
                             "billing_cycle": "MENSAL", "start_date": "2026-03-01", "payment_date": "2026-10-05"}
    assert (body["revenue"], body["quantity"], body["sales_count"]) == ("925.00", 50, 2)
    assert (body["average_ticket"], body["average_price_per_meal"], body["revenue_share_percent"]) == (
        "462.50", "18.50", "60.26")
    assert "net_profit" not in body
    assert len(body["daily"]) == 30
    assert body["daily"][0] == {"date": "2026-09-01", "revenue": "740.00", "quantity": 40, "sales_count": 1}
    assert [s["sale_date"] for s in body["recent_sales"]] == ["2026-09-30", "2026-09-01"]
    comparison = body["comparison"]
    assert comparison["previous_period"]["start_date"] == "2026-08-02"
    assert comparison["previous_period"]["end_date"] == "2026-08-31"
    assert comparison["revenue"] == "370.00"
    assert comparison["revenue_change_percent"] == "150.00"


def test_customer_dashboard(api, ref):  # DSH-02
    body = api.ok(api.get(f"/dashboard/customers/{ref.customer_x['id']}"))
    assert body["buyer"]["type"] == "CUSTOMER"
    assert (body["revenue"], body["quantity"], body["average_price_per_meal"]) == ("110.00", 5, "22.00")
    assert body["comparison"]["revenue_change_percent"] is None


def test_buyer_dashboard_not_found(api):
    assert api.get("/dashboard/companies/999999").status_code == 404
    assert api.get("/dashboard/customers/999999").status_code == 404


def test_inactive_company_dashboard(api, ref):
    api.ok(api.post(f"/companies/{ref.company_b['id']}/deactivate", {"version": ref.company_b["version"]}))
    body = api.ok(api.get(f"/dashboard/companies/{ref.company_b['id']}"))
    assert body["buyer"]["is_active"] is False
    assert body["revenue"] == "500.00"


# ---------- Histórico ----------

def test_history_all(api, ref):  # HIS-01
    body = api.ok(api.get("/history", params={"page_size": 100}))
    assert body["total"] == 7
    # Mesmo dia: custos antes das vendas (desempate estável).
    assert [(i["date"], i["kind"]) for i in body["items"]][:3] == [
        ("2026-09-30", "COST"), ("2026-09-30", "SALE"), ("2026-09-20", "SALE")]
    dates = [i["date"] for i in body["items"]]
    assert dates == sorted(dates, reverse=True)
    sale = next(i for i in body["items"] if i["kind"] == "SALE" and i["date"] == "2026-09-15")
    assert sale["sale"] == {"buyer": {"type": "COMPANY", "id": ref.company_b["id"], "name": "Empresa B"},
                            "quantity": 25, "unit_price": "20.00", "subtotal": "500.00",
                            "delivery_type": "OBRA", "payment_status": "PENDENTE"}
    assert sale["cost"] is None and sale["amount"] == "500.00"
    cost = next(i for i in body["items"] if i["kind"] == "COST" and i["date"] == "2026-09-05")
    assert cost["cost"]["category"]["name"] == "Aluguel"
    assert cost["cost"]["cost_type"] == "CUSTO_FIXO" and cost["sale"] is None
    assert body["totals"] == {"sales_total": "1535.00", "sales_quantity": 80, "sales_count": 4,
                              "sales_pending_total": "1535.00", "costs_total": "733.33", "costs_count": 3}


def test_history_buyer_filters_only_sales(api, ref):  # HIS-02
    body = api.ok(api.get("/history", params={"company_id": ref.company_a["id"]}))
    assert body["total"] == 2 and all(i["kind"] == "SALE" for i in body["items"])
    assert body["totals"]["sales_total"] == "925.00" and body["totals"]["costs_total"] == "0.00"
    customers = api.ok(api.get("/history", params={"buyer_type": "CUSTOMER"}))
    assert customers["total"] == 1 and customers["items"][0]["sale"]["buyer"]["name"] == "Cliente X"
    only_cost_with_buyer = api.ok(api.get("/history", params={"type": "COST", "company_id": ref.company_a["id"]}))
    assert only_cost_with_buyer["total"] == 0


def test_history_billing_closing(api, ref):  # HIS-03: fechamento quinzenal
    make_sale(api, ref.company_b, "COMPANY", "20.00", 10, "2026-09-02")
    first_half = api.ok(api.get("/history", params={"company_id": ref.company_b["id"], "start_date": "2026-09-01",
                                                    "end_date": "2026-09-15"}))
    assert first_half["totals"]["sales_total"] == "700.00"
    assert first_half["totals"]["sales_quantity"] == 35
    second_half = api.ok(api.get("/history", params={"company_id": ref.company_b["id"], "start_date": "2026-09-16",
                                                     "end_date": "2026-09-30"}))
    assert second_half["totals"]["sales_total"] == "0.00"


def test_history_type_and_cost_filters(api, ref):
    costs = api.ok(api.get("/history", params={"type": "COST"}))
    assert costs["total"] == 3 and costs["totals"]["sales_total"] == "0.00"
    fixed = api.ok(api.get("/history", params={"cost_type": "CUSTO_FIXO"}))
    assert fixed["total"] == 1 and fixed["totals"]["costs_total"] == "300.00"
    sales = api.ok(api.get("/history", params={"type": "SALE", "start_date": "2026-09-30",
                                               "end_date": "2026-09-30"}))
    assert sales["total"] == 1 and sales["totals"]["sales_total"] == "185.00"


def test_history_sort_and_pagination(api, ref):
    by_amount = api.ok(api.get("/history", params={"sort": "amount", "order": "desc", "page_size": 3}))
    assert [i["amount"] for i in by_amount["items"]] == ["740.00", "500.00", "400.00"]
    assert by_amount["pages"] == 3
    last = api.ok(api.get("/history", params={"sort": "amount", "order": "desc", "page_size": 3, "page": 3}))
    assert [i["amount"] for i in last["items"]] == ["33.33"]
    asc = api.ok(api.get("/history", params={"sort": "date", "order": "asc", "page_size": 1}))
    assert asc["items"][0]["date"] == "2026-09-01"
    assert api.get("/history", params={"sort": "senha"}).status_code == 422
    assert api.get("/history", params={"type": "OUTRO"}).status_code == 422
    assert api.get("/history", params={"start_date": "2026-09-10", "end_date": "2026-09-01"}).status_code == 422


def test_history_excludes_deleted(api, ref):
    api.delete(f"/sales/{ref.sales[0]['id']}")
    make_cost(api, ref.categories["Gás"], "10.00", "2026-09-10")
    body = api.ok(api.get("/history", params={"page_size": 100}))
    assert body["total"] == 7
    assert body["totals"]["sales_total"] == "795.00"
    assert body["totals"]["costs_total"] == "743.33"


def test_openapi_has_phase3_routes(client):  # API-05
    paths = client.get("/api/openapi.json").json()["paths"]
    for p in ["/api/v1/history", "/api/v1/dashboard/summary", "/api/v1/dashboard/daily",
              "/api/v1/dashboard/by-buyer", "/api/v1/dashboard/sales-by-company-daily",
              "/api/v1/dashboard/companies/{company_id}", "/api/v1/dashboard/customers/{customer_id}"]:
        assert p in paths
