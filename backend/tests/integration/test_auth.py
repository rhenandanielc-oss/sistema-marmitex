from datetime import timedelta

import pytest

from app.core import clock
from app.models import AuditLog, User
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, FIXED_NOW


def login(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_success_audited_and_last_login(client, admin, db):  # AUT-01
    resp = login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ADMIN_EMAIL
    assert body["user"]["role"] == "ADMIN"
    assert "password_hash" not in body["user"]
    db.refresh(admin)
    assert admin.last_login_at is not None
    assert db.query(AuditLog).filter_by(action="LOGIN_SUCCESS", user_id=admin.id).count() == 1


def test_login_email_case_insensitive(client, admin):
    assert login(client, email=ADMIN_EMAIL.upper()).status_code == 200


def test_login_failures_same_message(client, admin, db):  # AUT-02
    wrong_password = login(client, password="errada-123")
    unknown_email = login(client, email="ninguem@marmitex-teste.com.br")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert db.query(AuditLog).filter_by(action="LOGIN_FAILED").count() == 2


def test_login_rate_limit(client, admin):  # AUT-03
    for _ in range(5):
        assert login(client, password="errada-123").status_code == 401
    resp = login(client)
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "TOO_MANY_REQUESTS"


def test_inactive_user_cannot_login(client, admin, db):  # AUT-04
    admin.is_active = False
    db.commit()
    assert login(client).status_code == 401


@pytest.mark.parametrize("header", [None, "Bearer invalido", "Basic abc"])
def test_invalid_or_missing_token(client, admin, header):  # AUT-05
    headers = {"Authorization": header} if header else {}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_expired_token(client, auth):  # AUT-05
    clock.set_now_provider(lambda: FIXED_NOW + timedelta(hours=9))
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401


def test_logout_revokes_token(client, auth, db):  # AUT-06
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=auth).status_code == 204
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401
    assert db.query(AuditLog).filter_by(action="LOGOUT").count() == 1


def test_deactivating_user_revokes_sessions(client, api, db):  # AUT-07
    other = api.ok(api.post("/users", {"name": "Sócio", "email": "socio@marmitex-teste.com.br",
                                       "password": "outra-senha-1"}), 201)
    other_token = login(client, "socio@marmitex-teste.com.br", "outra-senha-1").json()["access_token"]
    other_auth = {"Authorization": f"Bearer {other_token}"}
    assert client.get("/api/v1/auth/me", headers=other_auth).status_code == 200
    api.ok(api.post(f"/users/{other['id']}/deactivate"))
    assert client.get("/api/v1/auth/me", headers=other_auth).status_code == 401


def test_cannot_deactivate_self_or_last_admin(api, admin):  # AUT-09
    resp = api.post(f"/users/{admin.id}/deactivate")
    assert resp.status_code == 409


def test_password_is_hashed_and_never_exposed(api, admin, db):  # AUT-10
    created = api.ok(api.post("/users", {"name": "Novo", "email": "novo@marmitex-teste.com.br",
                                         "password": "senha-nova-123"}), 201)
    assert "password" not in created and "password_hash" not in created
    user = db.get(User, created["id"])
    assert user.password_hash.startswith("$argon2id$")
    for log in db.query(AuditLog).all():
        dumped = str(log.before_data) + str(log.after_data)
        assert "password" not in dumped and "argon2" not in dumped


def test_change_password(client, api):
    resp = api.post("/auth/change-password", {"current_password": "errada", "new_password": "nova-senha-123"})
    assert resp.status_code == 422
    assert api.post("/auth/change-password", {"current_password": ADMIN_PASSWORD,
                                              "new_password": "nova-senha-123"}).status_code == 204
    assert login(client, password="nova-senha-123").status_code == 200


def test_users_crud_and_duplicate_email(api):
    created = api.ok(api.post("/users", {"name": "Maria", "email": "maria@marmitex-teste.com.br",
                                         "password": "senha-123-ok"}), 201)
    assert created["role"] == "ADMIN"
    dup = api.post("/users", {"name": "Outra", "email": "MARIA@marmitex-teste.com.br", "password": "senha-123-ok"})
    assert dup.status_code == 409
    updated = api.ok(api.patch(f"/users/{created['id']}", {"name": "Maria Silva", "version": created["version"]}))
    assert updated["name"] == "Maria Silva"
    assert updated["version"] == created["version"] + 1
    stale = api.patch(f"/users/{created['id']}", {"name": "X Y", "version": created["version"]})
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"
    listing = api.ok(api.get("/users", params={"q": "maria"}))
    assert listing["total"] == 1


def test_all_protected_routes_require_auth(client):  # AUT-08
    schema = client.get("/api/openapi.json").json()
    public = {"/api/v1/auth/login", "/api/v1/health/live", "/api/v1/health/ready"}
    checked = 0
    for path, methods in schema["paths"].items():
        if path in public:
            continue
        concrete = path.replace("{", "").replace("}", "").replace("_id", "1")
        concrete = "/".join("1" if seg.endswith("id") else seg for seg in concrete.split("/"))
        for method in methods:
            resp = client.request(method.upper(), concrete, json={})
            assert resp.status_code == 401, f"{method.upper()} {path} -> {resp.status_code}"
            checked += 1
    assert checked > 20
