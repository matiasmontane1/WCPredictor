from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    ODDS_API_KEY: str = ""
    FOOTBALL_DATA_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    ADMIN_PASSWORD: str = "admin"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


settings = Settings()
