from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VAULT_INBOX_",
        env_file=".env",
        extra="ignore",
    )

    database_path: Path = Field(default=Path("/data/vault-inbox.sqlite3"))
    vault_root: Path = Field(default=Path("/vault"))
    app_repo_root: Path = Field(default=Path("/app"))
    public_base_url: str = "https://inbox.ethan-herring.com"
    ollama_base_url: str = "http://192.168.1.185:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    codex_enabled: bool = False
    codex_binary: str = "codex"
    codex_timeout_seconds: int = 900
    smtp_enabled: bool = True
    smtp_host: str = "smtp-relay"
    smtp_port: int = 25
    smtp_from: str = "vault-inbox@ethan-herring.com"
    smtp_to: str = "admin@ethan-herring.com"
    raw_log_retention_days: int = 7
    worker_enabled: bool = True
    worker_interval_seconds: float = 5.0
    worker_stale_running_seconds: int = 1800
    docs_enabled: bool = False
    health_details_enabled: bool = False
    cors_allowed_origins: str = ""
    url_ingest_allow_private_networks: bool = False

    def cors_origins(self) -> list[str]:
        if self.cors_allowed_origins.strip():
            return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]
        return [
            self.public_base_url.rstrip("/"),
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
