"""Infraestrutura de testes (TEST-PLAN.md seção 1).

* Banco PostgreSQL de teste separado (TEST_DATABASE_URL), criado e migrado uma vez por sessão.
* Cada teste roda dentro de uma transação revertida ao final.
* Relógio do negócio fixado em 2026-09-30 12:00 (America/Sao_Paulo).
"""

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import psycopg
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.orm import Session

from alembic import command
from app.core import clock
from app.core.db import get_db
from app.core.security import hash_password, login_rate_limiter
from app.main import app
from app.models import User

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://marmitex:marmitex_dev@localhost:5432/marmitex_test"
)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2026-09-30 12:00 em São Paulo (UTC-3) — quarta-feira.
FIXED_NOW = datetime(2026, 9, 30, 15, 0, tzinfo=UTC)
ADMIN_EMAIL = "admin@marmitex-teste.com.br"
ADMIN_PASSWORD = "senha-forte-123"


def recreate_database(url: str) -> None:
    u = make_url(url)
    admin_dsn = f"host={u.host} port={u.port or 5432} user={u.username} password={u.password} dbname=postgres"
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{u.database}" WITH (FORCE)')
        conn.execute(f'CREATE DATABASE "{u.database}"')


def alembic_config(connection: Connection | None = None, url: str | None = None) -> Config:
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    if connection is not None:
        cfg.attributes["connection"] = connection
    if url is not None:
        cfg.attributes["database_url"] = url
    return cfg


@pytest.fixture(scope="session")
def engine():
    recreate_database(TEST_DATABASE_URL)
    eng = create_engine(TEST_DATABASE_URL)
    with eng.begin() as conn:
        command.upgrade(alembic_config(conn), "head")
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", autoflush=False,
                      expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def fixed_clock() -> Iterator[None]:
    clock.set_now_provider(lambda: FIXED_NOW)
    login_rate_limiter.reset()
    yield
    clock.reset()
    login_rate_limiter.reset()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin(db: Session) -> User:
    user = User(name="Admin Teste", email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), role="ADMIN")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def token(client: TestClient, admin: User) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class Api:
    """Cliente autenticado com atalhos."""

    def __init__(self, client: TestClient, headers: dict[str, str]):
        self.client = client
        self.headers = headers

    def get(self, url: str, **kw: Any):
        return self.client.get("/api/v1" + url, headers=self.headers, **kw)

    def post(self, url: str, json: Any = None, **kw: Any):
        return self.client.post("/api/v1" + url, json=json, headers=self.headers, **kw)

    def patch(self, url: str, json: Any = None, **kw: Any):
        return self.client.patch("/api/v1" + url, json=json, headers=self.headers, **kw)

    def delete(self, url: str, **kw: Any):
        return self.client.delete("/api/v1" + url, headers=self.headers, **kw)

    def ok(self, resp, status: int = 200) -> Any:
        assert resp.status_code == status, resp.text
        return resp.json() if resp.content else None


@pytest.fixture
def api(client: TestClient, auth: dict[str, str]) -> Api:
    return Api(client, auth)
