"""Custos (TEST-PLAN.md seção 4) e custos acumulados (R-CUS-7, R-CUS-8)."""

from app.models import AuditLog
from tests.integration.helpers import categories_by_name, make_cost


def test_create_cost_default_today(api):  # CUS-01
    cats = categories_by_name(api)
    cost = make_cost(api, cats["Ingredientes"], "150.00")
    assert cost["cost_date"] == "2026-09-30"
    assert cost["amount"] == "150.00"
    assert cost["category"]["name"] == "Ingredientes"
    assert cost["cost_type"] == "CUSTO_DIARIO"


def test_create_cost_past_date(api):  # CUS-02
    cost = make_cost(api, categories_by_name(api)["Aluguel"], "3000.00", "2026-09-05")
    assert cost["cost_date"] == "2026-09-05"


def test_future_date_rejected(api):  # CUS-03
    cat = categories_by_name(api)["Gás"]
    resp = api.post("/costs", {"category_id": cat["id"], "cost_type": "CUSTO_FIXO", "amount": "10.00",
                               "cost_date": "2026-10-01"})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "cost_date"


def test_invalid_amounts(api):  # CUS-04
    cat = categories_by_name(api)["Gás"]
    for amount in ["0", "-5.00", "1.234", "10000000.00"]:
        resp = api.post("/costs", {"category_id": cat["id"], "cost_type": "CUSTO_FIXO", "amount": amount})
        assert resp.status_code == 422, amount


def test_inactive_or_missing_category(api):  # CUS-05
    cat = categories_by_name(api)["Gasolina"]
    api.ok(api.post(f"/cost-categories/{cat['id']}/deactivate", {"version": cat["version"]}))
    resp = api.post("/costs", {"category_id": cat["id"], "cost_type": "CUSTO_DIARIO", "amount": "10.00"})
    assert resp.status_code == 422
    resp = api.post("/costs", {"category_id": 999999, "cost_type": "CUSTO_DIARIO", "amount": "10.00"})
    assert resp.status_code == 422


def test_type_must_match_category(api):  # CUS-06
    cat = categories_by_name(api)["Aluguel"]
    resp = api.post("/costs", {"category_id": cat["id"], "cost_type": "CUSTO_DIARIO", "amount": "10.00"})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "cost_type"
    assert api.post("/costs", {"category_id": cat["id"], "cost_type": "MENSAL", "amount": "1.00"}).status_code == 422


def test_edit_and_delete_cost(api, db):  # CUS-07
    cats = categories_by_name(api)
    cost = make_cost(api, cats["Ingredientes"], "100.00", "2026-09-10")
    edited = api.ok(api.patch(f"/costs/{cost['id']}", {"amount": "120.50", "version": cost["version"]}))
    assert edited["amount"] == "120.50" and edited["version"] == cost["version"] + 1
    assert api.patch(f"/costs/{cost['id']}", {"amount": "1.00", "version": cost["version"]}).status_code == 409
    moved = api.ok(api.patch(f"/costs/{cost['id']}", {"category_id": cats["Aluguel"]["id"],
                                                      "cost_type": "CUSTO_FIXO", "version": edited["version"]}))
    assert moved["cost_type"] == "CUSTO_FIXO" and moved["category"]["name"] == "Aluguel"
    mismatch = api.patch(f"/costs/{cost['id']}", {"category_id": cats["Gasolina"]["id"], "version": moved["version"]})
    assert mismatch.status_code == 422
    assert api.delete(f"/costs/{cost['id']}").status_code == 204
    assert api.get(f"/costs/{cost['id']}").status_code == 404
    actions = [log.action for log in db.query(AuditLog).filter_by(entity_type="cost").order_by(AuditLog.id)]
    assert actions == ["CREATE", "UPDATE", "UPDATE", "DELETE"]


def test_keep_deactivated_category_when_editing(api):  # R-CUS-2
    cat = categories_by_name(api)["Equipamentos"]
    cost = make_cost(api, cat, "80.00", "2026-09-10")
    api.ok(api.post(f"/cost-categories/{cat['id']}/deactivate", {"version": cat["version"]}))
    edited = api.ok(api.patch(f"/costs/{cost['id']}", {"amount": "90.00", "version": cost["version"]}))
    assert edited["amount"] == "90.00"


def test_new_category_available_immediately(api):  # CUS-08
    cat = api.ok(api.post("/cost-categories", {"name": "Descartáveis", "cost_type": "CUSTO_DIARIO"}), 201)
    cost = make_cost(api, cat, "45.90")
    assert cost["category"]["name"] == "Descartáveis"


def test_category_type_change_blocked_with_costs(api):  # CAD-10
    cat = api.ok(api.post("/cost-categories", {"name": "Internet", "cost_type": "CUSTO_FIXO"}), 201)
    make_cost(api, cat, "99.90")
    resp = api.patch(f"/cost-categories/{cat['id']}", {"cost_type": "CUSTO_DIARIO", "version": cat["version"]})
    assert resp.status_code == 409


def _reference_costs(api):
    cats = categories_by_name(api)
    make_cost(api, cats["Ingredientes"], "400.00", "2026-09-01")
    make_cost(api, cats["Aluguel"], "300.00", "2026-09-05")
    make_cost(api, cats["Embalagens"], "33.33", "2026-09-30")
    make_cost(api, cats["Gás"], "50.00", "2026-08-31")  # fora do mês


def test_running_totals(api):  # FIN-23
    _reference_costs(api)
    page = api.ok(api.get("/costs", params={"start_date": "2026-09-01", "end_date": "2026-09-30",
                                            "sort": "cost_date", "order": "asc"}))
    assert [(c["amount"], c["running_total"]) for c in page["items"]] == [
        ("400.00", "400.00"), ("300.00", "700.00"), ("33.33", "733.33")]
    assert page["totals"] == {"daily_costs": "433.33", "fixed_costs": "300.00", "total_costs": "733.33",
                              "count": 3}
    desc = api.ok(api.get("/costs", params={"start_date": "2026-09-01", "end_date": "2026-09-30"}))
    assert [c["running_total"] for c in desc["items"]] == ["733.33", "700.00", "400.00"]
    second_page = api.ok(api.get("/costs", params={"start_date": "2026-09-01", "end_date": "2026-09-30",
                                                   "page_size": 2, "page": 2}))
    assert [c["running_total"] for c in second_page["items"]] == ["400.00"]
    assert second_page["pages"] == 2
    by_amount = api.ok(api.get("/costs", params={"start_date": "2026-09-01", "sort": "amount", "order": "asc"}))
    assert [(c["amount"], c["running_total"]) for c in by_amount["items"]][0] == ("33.33", "733.33")
    all_time = api.ok(api.get("/costs", params={"order": "asc", "sort": "cost_date"}))
    assert all_time["items"][-1]["running_total"] == "783.33"


def test_running_totals_filtered_by_type(api):
    _reference_costs(api)
    daily = api.ok(api.get("/costs", params={"cost_type": "CUSTO_DIARIO", "start_date": "2026-09-01",
                                             "order": "asc"}))
    assert [c["running_total"] for c in daily["items"]] == ["400.00", "433.33"]
    assert daily["totals"]["total_costs"] == "433.33"


def test_cost_summary_month_grows_with_each_cost(api):  # FIN-29 / R-CUS-8
    summary = api.ok(api.get("/costs/summary"))
    assert summary["period"] == {"preset": "month", "start_date": "2026-09-01", "end_date": "2026-09-30",
                                 "days": 30}
    assert summary["total_costs"] == "0.00" and summary["count"] == 0
    _reference_costs(api)
    summary = api.ok(api.get("/costs/summary"))
    assert (summary["daily_costs"], summary["fixed_costs"], summary["total_costs"]) == ("433.33", "300.00", "733.33")
    make_cost(api, categories_by_name(api)["Gasolina"], "66.67")
    assert api.ok(api.get("/costs/summary"))["total_costs"] == "800.00"
    last_month = api.ok(api.get("/costs/summary", params={"period": "last_month"}))
    assert last_month["total_costs"] == "50.00"
    custom = api.ok(api.get("/costs/summary", params={"period": "custom", "start_date": "2026-09-05",
                                                      "end_date": "2026-09-05"}))
    assert custom["total_costs"] == "300.00"
    assert api.get("/costs/summary", params={"period": "custom"}).status_code == 422


def test_deleted_cost_leaves_totals(api):  # FIN-18
    cost = make_cost(api, categories_by_name(api)["Ingredientes"], "100.00")
    api.delete(f"/costs/{cost['id']}")
    assert api.ok(api.get("/costs/summary"))["total_costs"] == "0.00"
    assert api.ok(api.get("/costs"))["total"] == 0
