import pytest
from pydantic import ValidationError

from app.core.config import Settings

SAFE_SECRET = "Xk3v9-segredo-aleatorio-de-producao-com-48-caracteres-ok"
SAFE_DB = "postgresql+psycopg://marmitex:S3nh4-Forte@db:5432/marmitex"


def test_production_rejects_example_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", database_url=SAFE_DB)
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", database_url=SAFE_DB,
                 jwt_secret="troque-por-um-segredo-longo-e-aleatorio-com-pelo-menos-32-caracteres")


def test_production_rejects_example_db_password():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(environment="production", jwt_secret=SAFE_SECRET,
                 database_url="postgresql+psycopg://marmitex:troque-esta-senha@db:5432/marmitex")


def test_production_ok_and_docs_disabled_by_default():
    s = Settings(environment="production", jwt_secret=SAFE_SECRET, database_url=SAFE_DB)
    assert s.api_docs_enabled is False
    assert Settings(environment="production", jwt_secret=SAFE_SECRET, database_url=SAFE_DB,
                    enable_api_docs=True).api_docs_enabled is True


def test_development_allows_defaults():
    s = Settings(environment="development")
    assert s.api_docs_enabled is True


def test_short_secret_rejected():
    with pytest.raises(ValidationError):
        Settings(jwt_secret="curto")
