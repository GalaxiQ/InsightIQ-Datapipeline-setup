from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


# Repository root (…/InsightsIQ-setup). Computed once so defaults work
# regardless of the current working directory when the API process starts.
BASE_DIR = Path(__file__).resolve().parents[4]

class Settings(BaseSettings):
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # MUST MATCH remote production postgres
    MASTER_DB_URL: str = Field(
        default="postgresql+asyncpg://postgres:galaxiq@66.135.22.167:5432/galaxiq_tenants"
    )

    API_KEY: str | None = None
    ALLOWED_DOMAINS: list[str] = ["social", "web", "crm", "ads"]
    # Absolute defaults so uvicorn can be started from any path
    DBT_PROJECT_DIR: str = str(BASE_DIR / "services/dbt")
    # DBT_BIN: str = str(BASE_DIR / "venv-dbt/bin/dbt")
    DBT_BIN: str = "/Users/nitizz/Desktop/InsightsIQ-setup/venv-dbt/bin/dbt"


    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = "https://galaxiq-ai-resource.cognitiveservices.azure.com/"
    AZURE_OPENAI_API_KEY: str = "4iEDEZPtrFkQrOV8GBc6OqrTOFiRlcRcuIJOgBEId1DuYOd1U1qcJQQJ99CAACHYHv6XJ3w3AAAAACOGPPrX"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-5.2-chat"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    class Config:
        env_file = ".env"

settings = Settings()
