from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from app.core.settings import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def validate_api_key(api_key: str = Security(api_key_header)):
    if not settings.API_KEY:
        return True  # Security disabled

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return True
