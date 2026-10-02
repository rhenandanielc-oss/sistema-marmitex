"""Vendas (TEST-PLAN.md seção 3)."""

import pytest

from app.models import AuditLog, Sale
from tests.integration.helpers import make_sale


@pytest.fixture
def company(api):
    return api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)


@pytest.fixture
def customer(api):
    return api.ok(api.post("/customers", {"name": "João da Obra"}), 201)


def test_create_company_sale_default_today(api, company, db):  # VEN-01
    sale = make_sale(api, company, "COMPANY", "18.50", 40)
    assert sale["sale_date"] == "2026-09-30"
    assert sale["subtotal"] == "740.00"
    assert sale["unit_price"] == "18.50"
    assert sale["buyer"] == {"type": "COMPANY", "id": company["id"], "name": "Construtora Alfa"}
    assert sale["created_by"]["name"] == "Admin Teste"
    log = db.query(AuditLog).filter_by(entity_type="sale", action="CREATE").one()
    assert log.after_data["subtotal"] == "740.00"


def test_create_customer_sale_with_past_date(api, customer):  # VEN-02
    sale = make_sale(api, customer, "CUSTOMER", "22.00", 5, "2026-09-10")
    assert sale["sale_date"] == "2026-09-10"
    assert sale["buyer"]["type"] == "CUSTOMER"
    assert sale["subtotal"] == "110.00"


def test_future_date_rejected(api, company):  # VEN-03
    resp = api.post("/sales", {"buyer_type": "COMPANY", "company_id": company["id"], "unit_price": "10.00",
                               "quantity": 1, "sale_date": "2026-10-01"})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "sale_date"


def test_subtotal_from_client_rejected(api, company):  # VEN-04
    resp = api.post("/sales", {"buyer_type": "COMPANY", "company_id": company["id"], "unit_price": "10.00",
                               "quantity": 1, "subtotal": "1.00"})
    assert resp.status_code == 422


@pytest.mark.parametrize("buyer", [
    {"buyer_type": "COMPANY"},
    {"buyer_type": "COMPANY", "customer_id": 1},
    {"buyer_type": "CUSTOMER", "company_id": 1},
    {"buyer_type": "COMPANY", "company_id": 1, "customer_id": 1},
    {"buyer_type": "OUTRO", "company_id": 1},
    {"company_id": 1},
])
def test_single_buyer_rules(api, buyer):  # VEN-05
    resp = api.post("/sales", {**buyer, "unit_price": "10.00", "quantity": 1})
    assert resp.status_code == 422


def test_database_enforces_single_buyer(db, company, customer):  # VEN-05 (CHECK no banco)
    from datetime import date
    from decimal import Decimal

    from sqlalchemy.exc import IntegrityError

    db.add(Sale(buyer_type="COMPANY", company_id=company["id"], customer_id=customer["id"],
                sale_date=date(2026, 9, 1), unit_price=Decimal("1.00"), quantity=1, subtotal=Decimal("1.00")))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_database_enforces_subtotal_formula(db, company):
    from datetime import date
    from decimal import Decimal

    from sqlalchemy.exc import IntegrityError

    db.add(Sale(buyer_type="COMPANY", company_id=company["id"], sale_date=date(2026, 9, 1),
                unit_price=Decimal("10.00"), quantity=2, subtotal=Decimal("19.99")))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("price", ["0", "-1.00", "10.001", "10000.00", "abc"])
def test_invalid_price(api, company, price):  # VEN-06
    resp = api.post("/sales", {"buyer_type": "COMPANY", "company_id": company["id"], "unit_price": price,
                               "quantity": 1})
    assert resp.status_code == 422


@pytest.mark.parametrize("qty", [0, -1, 1.5, 10001])
def test_invalid_quantity(api, company, qty):  # VEN-07
    resp = api.post("/sales", {"buyer_type": "COMPANY", "company_id": company["id"], "unit_price": "10.00",
                               "quantity": qty})
    assert resp.status_code == 422


def test_inactive_or_missing_buyer(api, company, customer):  # VEN-08
    api.ok(api.post(f"/companies/{company['id']}/deactivate", {"version": company["version"]}))
    resp = api.post("/sales", {"buyer_type": "COMPANY", "company_id": company["id"], "unit_price": "10.00",
                               "quantity": 1})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "company_id"
    resp = api.post("/sales", {"buyer_type": "CUSTOMER", "customer_id": 999999, "unit_price": "10.00",
                               "quantity": 1})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "customer_id"


def test_edit_recalculates_subtotal_and_audits(api, company, db):  # VEN-09
    sale = make_sale(api, company, "COMPANY", "18.50", 40)
    edited = api.ok(api.patch(f"/sales/{sale['id']}", {"quantity": 50, "unit_price": "20.00",
                                                       "sale_date": "2026-09-29", "version": sale["version"]}))
    assert edited["subtotal"] == "1000.00"
    assert edited["sale_date"] == "2026-09-29"
    assert edited["version"] == sale["version"] + 1
    log = db.query(AuditLog).filter_by(entity_type="sale", action="UPDATE").one()
    assert log.before_data["subtotal"] == "740.00" and log.after_data["subtotal"] == "1000.00"
    assert log.before_data["sale_date"] == "2026-09-30"


def test_edit_future_date_rejected(api, company):
    sale = make_sale(api, company, "COMPANY", "10.00", 1)
    assert api.patch(f"/sales/{sale['id']}", {"sale_date": "2026-12-01", "version": 1}).status_code == 422


def test_version_conflict(api, company):  # VEN-10
    sale = make_sale(api, company, "COMPANY", "10.00", 1)
    api.ok(api.patch(f"/sales/{sale['id']}", {"quantity": 2, "version": sale["version"]}))
    resp = api.patch(f"/sales/{sale['id']}", {"quantity": 3, "version": sale["version"]})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "VERSION_CONFLICT"


def test_change_buyer_company_to_customer(api, company, customer):  # VEN-11
    sale = make_sale(api, company, "COMPANY", "10.00", 2)
    edited = api.ok(api.patch(f"/sales/{sale['id']}", {"buyer_type": "CUSTOMER", "customer_id": customer["id"],
                                                       "version": sale["version"]}))
    assert edited["buyer"] == {"type": "CUSTOMER", "id": customer["id"], "name": "João da Obra"}
    missing_id = api.patch(f"/sales/{sale['id']}", {"buyer_type": "COMPANY", "version": edited["version"]})
    assert missing_id.status_code == 422


def test_delete_sale(api, company, db):  # VEN-12
    sale = make_sale(api, company, "COMPANY", "10.00", 2)
    assert api.delete(f"/sales/{sale['id']}").status_code == 204
    assert api.get(f"/sales/{sale['id']}").status_code == 404
    assert api.ok(api.get("/sales"))["total"] == 0
    assert db.query(AuditLog).filter_by(entity_type="sale", action="DELETE").count() == 1


def test_keep_deactivated_buyer_when_editing(api, company):  # VEN-13
    sale = make_sale(api, company, "COMPANY", "10.00", 2)
    api.ok(api.post(f"/companies/{company['id']}/deactivate", {"version": company["version"]}))
    edited = api.ok(api.patch(f"/sales/{sale['id']}", {"quantity": 3, "version": sale["version"]}))
    assert edited["subtotal"] == "30.00"
    same_buyer = api.ok(api.patch(f"/sales/{sale['id']}", {"buyer_type": "COMPANY", "company_id": company["id"],
                                                           "version": edited["version"]}))
    assert same_buyer["buyer"]["id"] == company["id"]


def test_list_sales_filters_and_sort(api, company, customer):
    make_sale(api, company, "COMPANY", "10.00", 1, "2026-09-01")
    make_sale(api, company, "COMPANY", "10.00", 5, "2026-09-15")
    make_sale(api, customer, "CUSTOMER", "12.00", 2, "2026-09-20")
    assert api.ok(api.get("/sales"))["total"] == 3
    assert api.ok(api.get("/sales", params={"buyer_type": "CUSTOMER"}))["total"] == 1
    assert api.ok(api.get("/sales", params={"company_id": company["id"]}))["total"] == 2
    inclusive = api.ok(api.get("/sales", params={"start_date": "2026-09-01", "end_date": "2026-09-15"}))
    assert inclusive["total"] == 2
    by_date = api.ok(api.get("/sales"))["items"]
    assert [s["sale_date"] for s in by_date] == ["2026-09-20", "2026-09-15", "2026-09-01"]
    by_qty = api.ok(api.get("/sales", params={"sort": "quantity", "order": "asc"}))["items"]
    assert [s["quantity"] for s in by_qty] == [1, 2, 5]
    by_buyer = api.ok(api.get("/sales", params={"sort": "buyer", "order": "asc"}))["items"]
    assert by_buyer[0]["buyer"]["name"] == "Construtora Alfa"
    assert api.get("/sales", params={"sort": "senha"}).status_code == 422
