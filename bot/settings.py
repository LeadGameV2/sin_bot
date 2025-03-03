from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

class _BaseSettings(BaseSettings):
    """Базовые настройки."""

    base_dir: Path = Path(__file__).parent.resolve()
    model_config = SettingsConfigDict(
        env_file=str(base_dir / ".env"), extra="ignore"
    )


class PostgresSettings(_BaseSettings):
    """Настройки постгреса."""

    model_config = SettingsConfigDict(env_prefix="postgres_")
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str
    db_name: str = "sins_database"

class Settings(BaseSettings):
    """Настройки проекта."""

    root_dir: Path = Path(__file__).parent.resolve()
    bot_token: str

    top_sins_per_page: int = 5

    postgres: PostgresSettings = PostgresSettings()

settings = Settings()
