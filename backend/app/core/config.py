from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-secret-change-me-dev-secret-change-me"
PLACEHOLDER_MARKERS = ("troque", "change-me", "changeme", "marmitex_dev")


class Settings(BaseSettings):
    """Configuração lida de variáveis de ambiente (ou do arquivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://marmitex:marmitex_dev@localhost:5432/marmitex"
    jwt_secret: str = Field(default=DEV_JWT_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    app_timezone: str = "America/Sao_Paulo"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    login_max_failures: int = 5
    login_failure_window_minutes: int = 15
    enable_api_docs: bool | None = None  # padrão: ligado fora de produção

    @model_validator(mode="after")
    def _production_safety(self) -> "Settings":
        if self.is_production:
            secret = self.jwt_secret.lower()
            if self.jwt_secret == DEV_JWT_SECRET or any(m in secret for m in PLACEHOLDER_MARKERS):
                raise ValueError("JWT_SECRET de exemplo em produção. Gere um segredo novo (veja INSTALL.md).")
            if any(m in self.database_url.lower() for m in PLACEHOLDER_MARKERS):
                raise ValueError("Senha de exemplo no DATABASE_URL em produção. Defina uma senha própria no .env.")
        return self

    @property
    def api_docs_enabled(self) -> bool:
        return (not self.is_production) if self.enable_api_docs is None else self.enable_api_docs

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
