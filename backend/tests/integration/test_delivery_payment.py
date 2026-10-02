"""Tipo de recebimento (retirada/entrega/obra) e situação de pagamento (pago/pendente)."""

from tests.integration.helpers import make_sale


def test_registry_default_delivery_type(api):
    company = api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)
    customer = api.ok(api.post("/customers", {"name": "João"}), 201)
    assert company["default_delivery_type"] == "OBRA"
    assert customer["default_delivery_type"] == "RETIRADA"
    delivery = api.ok(api.post("/customers", {"name": "Maria", "default_delivery_type": "ENTREGA"}), 201)
    assert delivery["default_delivery_type"] == "ENTREGA"
    assert api.post("/customers", {"name": "X Y", "default_delivery_type": "CORREIO"}).status_code == 422
    edited = api.ok(api.patch(f"/customers/{customer['id']}", {"default_delivery_type": "ENTREGA",
                                                               "version": customer["version"]}))
    assert edited["default_delivery_type"] == "ENTREGA"
    assert api.patch(f"/customers/{customer['id']}", {"default_delivery_type": None,
                                                      "version": edited["version"]}).status_code == 422
    # Separar clientes pelo tipo de recebimento.
    by_delivery = api.ok(api.get("/customers", params={"delivery_type": "ENTREGA"}))
    assert {c["name"] for c in by_delivery["items"]} == {"João", "Maria"}
    assert api.ok(api.get("/companies", params={"delivery_type": "RETIRADA"}))["total"] == 0


def test_sale_inherits_buyer_default_and_can_override(api):
    company = api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)
    customer = api.ok(api.post("/customers", {"name": "João", "default_delivery_type": "ENTREGA"}), 201)
    s1 = make_sale(api, company, "COMPANY", "18.50", 10)
    assert (s1["delivery_type"], s1["payment_status"]) == ("OBRA", "PENDENTE")
    s2 = make_sale(api, customer, "CUSTOMER", "22.00", 1)
    assert s2["delivery_type"] == "ENTREGA"
    s3 = make_sale(api, customer, "CUSTOMER", "22.00", 1, delivery_type="RETIRADA", payment_status="PAGO")
    assert (s3["delivery_type"], s3["payment_status"]) == ("RETIRADA", "PAGO")
    bad = api.post("/sales", {"buyer_type": "CUSTOMER", "customer_id": customer["id"], "unit_price": "1.00",
                              "quantity": 1, "payment_status": "TALVEZ"})
    assert bad.status_code == 422


def test_mark_sale_as_paid_is_audited(api, db):
    from app.models import AuditLog

    company = api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)
    sale = make_sale(api, company, "COMPANY", "18.50", 10)
    paid = api.ok(api.patch(f"/sales/{sale['id']}", {"payment_status": "PAGO", "version": sale["version"]}))
    assert paid["payment_status"] == "PAGO"
    assert paid["subtotal"] == "185.00"
    log = db.query(AuditLog).filter_by(entity_type="sale", action="UPDATE").one()
    assert log.before_data["payment_status"] == "PENDENTE" and log.after_data["payment_status"] == "PAGO"


def test_filters_and_pending_totals(api):
    company = api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)
    customer = api.ok(api.post("/customers", {"name": "João"}), 201)
    make_sale(api, company, "COMPANY", "20.00", 10, "2026-09-10", payment_status="PAGO")        # 200 pago, obra
    make_sale(api, company, "COMPANY", "20.00", 5, "2026-09-11")                                # 100 pendente, obra
    make_sale(api, customer, "CUSTOMER", "22.00", 2, "2026-09-12")                              # 44 pendente, retirada
    make_sale(api, customer, "CUSTOMER", "22.00", 1, "2026-09-13", delivery_type="ENTREGA")     # 22 pendente, entrega

    assert api.ok(api.get("/sales", params={"payment_status": "PENDENTE"}))["total"] == 3
    assert api.ok(api.get("/sales", params={"delivery_type": "RETIRADA"}))["total"] == 1

    history = api.ok(api.get("/history", params={"start_date": "2026-09-01"}))
    assert history["totals"]["sales_total"] == "366.00"
    assert history["totals"]["sales_pending_total"] == "166.00"
    pending_company = api.ok(api.get("/history", params={"company_id": company["id"], "payment_status": "PENDENTE"}))
    assert pending_company["totals"]["sales_total"] == "100.00"
    assert pending_company["items"][0]["sale"]["payment_status"] == "PENDENTE"
    paid_only = api.ok(api.get("/history", params={"payment_status": "PAGO"}))
    assert paid_only["totals"]["sales_pending_total"] == "0.00"
    assert all(i["kind"] == "SALE" for i in paid_only["items"])  # filtro de pagamento → só vendas
    delivery = api.ok(api.get("/history", params={"delivery_type": "ENTREGA"}))
    assert delivery["totals"]["sales_total"] == "22.00"

    summary = api.ok(api.get("/dashboard/summary"))
    assert summary["revenue"] == "366.00"            # receita conta tudo (pago ou não)
    assert summary["pending_revenue"] == "166.00"    # a receber
    by_buyer = {i["buyer"]["name"]: i for i in api.ok(api.get("/dashboard/by-buyer"))["items"]}
    assert by_buyer["Construtora Alfa"]["pending_revenue"] == "100.00"
    assert by_buyer["João"]["pending_revenue"] == "66.00"
    detail = api.ok(api.get(f"/dashboard/companies/{company['id']}"))
    assert (detail["revenue"], detail["pending_revenue"]) == ("300.00", "100.00")
