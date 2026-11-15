from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PENTETST-AI"
    app_version: str = "0.1.0"
    request_timeout: float = 10.0
    allowed_ports: list[int] = [80, 443]
    allow_private_targets: bool = False
    ai_provider: str = "heuristic"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    sqlite_database_path: str = "./data/pentest_ai.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
