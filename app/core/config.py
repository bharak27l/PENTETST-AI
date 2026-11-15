from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PENTETST-AI"
    app_version: str = "0.5.0"
    request_timeout: float = 10.0
    allowed_ports: list[int] = [80, 443]
    allow_private_targets: bool = False
    ai_provider: str = "heuristic"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    sqlite_database_path: str = "./data/pentest_ai.db"
    auth_secret: str = ""
    auth_token_ttl_seconds: int = 3600
    bootstrap_username: str = "admin"
    bootstrap_password: str = ""
    scheduler_enabled: bool = False
    scheduler_interval_seconds: int = 3600
    nuclei_enabled: bool = False
    zap_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
