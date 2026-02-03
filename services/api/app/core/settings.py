from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # MUST MATCH docker-compose env var
    MASTER_DB_URL: str = Field(
        default="postgresql+asyncpg://insightiq:insightiq@master_db:5432/master"
    )

    API_KEY: str | None = None
    ALLOWED_DOMAINS: list[str] = ["social", "web", "crm", "ads"]

    class Config:
        env_file = ".env"

settings = Settings()
