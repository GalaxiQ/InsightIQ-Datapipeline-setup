from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MASTER_DB_URL: str
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    MODEL_NAME: str = "gpt-5.2-chat"
    
    # Worker Configuration
    MAX_CONCURRENT_TENANTS: int = 5
    MAX_CONCURRENT_REQUESTS: int = 20
    POLL_INTERVAL_SECONDS: int = 10
    BATCH_SIZE: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
