from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração lida de variáveis de ambiente (ou do arquivo .env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://marmitex:marmitex_dev@localhost:5432/marmitex"
    jwt_secret: str = Field(default="dev-secret-change-me-dev-secret-change-me", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    app_timezone: str = "America/Sao_Paulo"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    login_max_failures: int = 5
    login_failure_window_minutes: int = 15

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
