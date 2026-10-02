import pytest

from app.models import AuditLog

VALID_CNPJ = "11.222.333/0001-81"
VALID_CNPJ_2 = "45.723.174/0001-10"
VALID_CPF = "529.982.247-25"


# ---------- Empresas ----------

def test_create_and_edit_company(api, db):  # CAD-01
    created = api.ok(api.post("/companies", {
        "name": "Construtora Alfa", "cnpj": VALID_CNPJ, "billing_cycle": "QUINZENAL",
        "start_date": "2026-03-01", "payment_date": "2026-10-05", "email": "obra@alfa.com",
        "location": "Obra Av. Paulista, 1000"}), 201)
    assert created["cnpj"] == "11222333000181"
    assert created["location"] == "Obra Av. Paulista, 1000"
    assert created["billing_cycle"] == "QUINZENAL"
    assert created["start_date"] == "2026-03-01"
    assert created["payment_date"] == "2026-10-05"
    assert created["is_active"] is True
    edited = api.ok(api.patch(f"/companies/{created['id']}", {"payment_date": "2026-10-20",
                                                              "version": created["version"]}))
    assert edited["payment_date"] == "2026-10-20"
    assert edited["start_date"] == "2026-03-01"
    logs = db.query(AuditLog).filter_by(entity_type="company", entity_id=str(created["id"])).all()
    assert [log.action for log in sorted(logs, key=lambda x: x.id)] == ["CREATE", "UPDATE"]
    update = [log for log in logs if log.action == "UPDATE"][0]
    assert update.before_data["payment_date"] == "2026-10-05"
    assert update.after_data["payment_date"] == "2026-10-20"


def test_company_defaults(api):
    created = api.ok(api.post("/companies", {"name": "Empreiteira Beta"}), 201)
    assert created["billing_cycle"] == "MENSAL"
    assert created["start_date"] is None and created["payment_date"] is None


def test_company_duplicates(api):  # CAD-02
    api.ok(api.post("/companies", {"name": "Construtora Alfa", "cnpj": VALID_CNPJ}), 201)
    assert api.post("/companies", {"name": "construtora ALFA"}).status_code == 409
    assert api.post("/companies", {"name": "Outra", "cnpj": "11222333000181"}).status_code == 409


@pytest.mark.parametrize("payload", [
    {"name": "X"},
    {"name": "Valida", "cnpj": "11.222.333/0001-00"},
    {"name": "Valida", "cnpj": "11111111111111"},
    {"name": "Valida", "billing_cycle": "SEMANAL"},
    {"name": "Valida", "email": "nao-e-email"},
    {"name": "Valida", "start_date": "31/12/2026"},
    {"name": "Valida", "campo_extra": 1},
])
def test_company_validation(api, payload):  # CAD-03
    assert api.post("/companies", payload).status_code == 422


def test_company_null_name_on_update(api):
    c = api.ok(api.post("/companies", {"name": "Alfa"}), 201)
    assert api.patch(f"/companies/{c['id']}", {"name": None, "version": c["version"]}).status_code == 422


def test_activate_deactivate_company(api):  # CAD-04
    c = api.ok(api.post("/companies", {"name": "Alfa"}), 201)
    off = api.ok(api.post(f"/companies/{c['id']}/deactivate", {"version": c["version"]}))
    assert off["is_active"] is False
    active = api.ok(api.get("/companies", params={"active": "true"}))
    assert all(i["id"] != c["id"] for i in active["items"])
    assert api.post(f"/companies/{c['id']}/activate", {"version": c["version"]}).status_code == 409
    on = api.ok(api.post(f"/companies/{c['id']}/activate", {"version": off["version"]}))
    assert on["is_active"] is True


def test_search_companies(api):  # CAD-05
    api.ok(api.post("/companies", {"name": "Construtora Alfa", "cnpj": VALID_CNPJ}), 201)
    api.ok(api.post("/companies", {"name": "Empreiteira Beta", "trade_name": "Beta Obras",
                                   "cnpj": VALID_CNPJ_2}), 201)
    assert api.ok(api.get("/companies", params={"q": "alfa"}))["total"] == 1
    assert api.ok(api.get("/companies", params={"q": "obras"}))["total"] == 1
    assert api.ok(api.get("/companies", params={"q": "45.723"}))["total"] == 1
    names = [i["name"] for i in api.ok(api.get("/companies", params={"sort": "name", "order": "desc"}))["items"]]
    assert names == ["Empreiteira Beta", "Construtora Alfa"]
    api.ok(api.post("/companies", {"name": "Gama Engenharia", "location": "Obra Shopping Norte"}), 201)
    assert api.ok(api.get("/companies", params={"q": "shopping"}))["total"] == 1


# ---------- Clientes avulsos ----------

def test_create_customer_independent(api):  # CAD-06
    created = api.ok(api.post("/customers", {
        "name": "João da Obra", "phone": "(11) 99999-0000", "location": "Obra Rua X",
        "billing_cycle": "MENSAL", "start_date": "2026-09-01", "payment_date": "2026-10-01"}), 201)
    assert created["start_date"] == "2026-09-01"
    assert created["payment_date"] == "2026-10-01"
    assert "company_id" not in created


def test_customer_names_not_unique_documents_unique(api):  # CAD-07
    api.ok(api.post("/customers", {"name": "João", "document": VALID_CPF}), 201)
    api.ok(api.post("/customers", {"name": "João"}), 201)
    assert api.post("/customers", {"name": "Outro", "document": "52998224725"}).status_code == 409
    assert api.post("/customers", {"name": "Outro", "document": "123.456.789-00"}).status_code == 422
    assert api.post("/customers", {"name": "Outro", "billing_cycle": "ANUAL"}).status_code == 422


def test_search_customers(api):  # CAD-08
    api.ok(api.post("/customers", {"name": "João", "phone": "11988887777", "location": "Obra Centro"}), 201)
    api.ok(api.post("/customers", {"name": "Pedro", "location": "Galpão"}), 201)
    assert api.ok(api.get("/customers", params={"q": "8888"}))["total"] == 1
    assert api.ok(api.get("/customers", params={"q": "centro"}))["total"] == 1
    assert api.ok(api.get("/customers", params={"q": "pedro"}))["total"] == 1


def test_customer_activation(api):
    c = api.ok(api.post("/customers", {"name": "João"}), 201)
    off = api.ok(api.post(f"/customers/{c['id']}/deactivate", {"version": c["version"]}))
    assert off["is_active"] is False
    assert api.ok(api.get("/customers", params={"active": "true"}))["total"] == 0


# ---------- Categorias ----------

def test_seeded_categories(api):  # CAD-11
    page = api.ok(api.get("/cost-categories", params={"page_size": 100}))
    by_name = {c["name"]: c["cost_type"] for c in page["items"]}
    assert by_name["Ingredientes"] == "CUSTO_DIARIO"
    assert by_name["Gasolina"] == "CUSTO_DIARIO"
    assert by_name["Energia elétrica"] == "CUSTO_FIXO"
    assert len(by_name) == 10


def test_category_crud(api):  # CAD-09
    cat = api.ok(api.post("/cost-categories", {"name": "Descartáveis", "cost_type": "CUSTO_DIARIO"}), 201)
    assert api.post("/cost-categories", {"name": "descartáveis", "cost_type": "CUSTO_FIXO"}).status_code == 409
    assert api.post("/cost-categories", {"name": "Outra", "cost_type": "MENSAL"}).status_code == 422
    edited = api.ok(api.patch(f"/cost-categories/{cat['id']}", {"name": "Copos descartáveis",
                                                                "version": cat["version"]}))
    off = api.ok(api.post(f"/cost-categories/{cat['id']}/deactivate", {"version": edited["version"]}))
    assert off["is_active"] is False
    assert api.ok(api.get("/cost-categories", params={"q": "copos"}))["total"] == 1
    fixed = api.ok(api.get("/cost-categories", params={"cost_type": "CUSTO_FIXO", "active": "true"}))
    assert fixed["total"] == 5


def test_category_type_change_without_costs(api):
    cat = api.ok(api.post("/cost-categories", {"name": "Internet", "cost_type": "CUSTO_DIARIO"}), 201)
    changed = api.ok(api.patch(f"/cost-categories/{cat['id']}", {"cost_type": "CUSTO_FIXO",
                                                                 "version": cat["version"]}))
    assert changed["cost_type"] == "CUSTO_FIXO"
