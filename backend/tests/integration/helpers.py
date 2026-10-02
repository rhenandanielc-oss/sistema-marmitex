"""Fábrica dos dados de referência (FINANCIAL-RULES.md seção 7) via API."""

from dataclasses import dataclass


@dataclass
class Reference:
    company_a: dict
    company_b: dict
    customer_x: dict
    categories: dict[str, dict]
    sales: list[dict]
    costs: list[dict]


def categories_by_name(api) -> dict[str, dict]:
    return {c["name"]: c for c in api.ok(api.get("/cost-categories", params={"page_size": 100}))["items"]}


def make_sale(api, buyer: dict, buyer_type: str, price: str, qty: int, day: str | None = None, **extra):
    payload = {"buyer_type": buyer_type, "unit_price": price, "quantity": qty, **extra}
    payload["company_id" if buyer_type == "COMPANY" else "customer_id"] = buyer["id"]
    if day:
        payload["sale_date"] = day
    return api.ok(api.post("/sales", payload), 201)


def make_cost(api, category: dict, amount: str, day: str | None = None, **extra):
    payload = {"category_id": category["id"], "cost_type": category["cost_type"], "amount": amount, **extra}
    if day:
        payload["cost_date"] = day
    return api.ok(api.post("/costs", payload), 201)


def build_reference(api) -> Reference:
    a = api.ok(api.post("/companies", {"name": "Empresa A"}), 201)
    b = api.ok(api.post("/companies", {"name": "Empresa B", "billing_cycle": "QUINZENAL"}), 201)
    x = api.ok(api.post("/customers", {"name": "Cliente X"}), 201)
    cats = categories_by_name(api)
    sales = [
        make_sale(api, a, "COMPANY", "18.50", 40, "2026-09-01"),
        make_sale(api, b, "COMPANY", "20.00", 25, "2026-09-15"),
        make_sale(api, x, "CUSTOMER", "22.00", 5, "2026-09-20"),
        make_sale(api, a, "COMPANY", "18.50", 10, "2026-09-30"),
    ]
    costs = [
        make_cost(api, cats["Ingredientes"], "400.00", "2026-09-01"),
        make_cost(api, cats["Aluguel"], "300.00", "2026-09-05"),
        make_cost(api, cats["Embalagens"], "33.33", "2026-09-30"),
    ]
    return Reference(a, b, x, cats, sales, costs)
