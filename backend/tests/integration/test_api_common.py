def test_health(client):  # API-06
    assert client.get("/api/v1/health/live").json() == {"status": "ok"}
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "up"


def test_openapi_lists_routes(client):  # API-05
    schema = client.get("/api/openapi.json").json()
    for path in ["/api/v1/auth/login", "/api/v1/companies", "/api/v1/customers", "/api/v1/cost-categories",
                 "/api/v1/users", "/api/v1/audit-logs"]:
        assert path in schema["paths"]


def test_error_format_and_request_id(api):  # API-03
    resp = api.post("/companies", {"name": ""}, )
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert set(err) == {"code", "message", "details", "request_id"}
    assert err["code"] == "VALIDATION_ERROR"
    assert err["details"][0]["field"] == "name"
    assert err["request_id"] == resp.headers["X-Request-ID"]


def test_not_found_format(api):
    resp = api.get("/companies/999999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_pagination_limits(api):  # API-01
    assert api.get("/companies", params={"page_size": 0}).status_code == 422
    assert api.get("/companies", params={"page_size": 101}).status_code == 422
    assert api.get("/companies", params={"page": 0}).status_code == 422


def test_pagination_counts(api):
    for i in range(5):
        api.ok(api.post("/companies", {"name": f"Empresa {i}"}), 201)
    page = api.ok(api.get("/companies", params={"page_size": 2, "page": 3}))
    assert page["total"] == 5 and page["pages"] == 3 and len(page["items"]) == 1


def test_invalid_sort(api):  # API-02
    resp = api.get("/companies", params={"sort": "senha"})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["field"] == "sort"


def test_audit_logs_listing(api):  # AUD-03
    api.ok(api.post("/companies", {"name": "Construtora Alfa"}), 201)
    logs = api.ok(api.get("/audit-logs", params={"entity_type": "company"}))
    assert logs["total"] == 1
    assert logs["items"][0]["action"] == "CREATE"
