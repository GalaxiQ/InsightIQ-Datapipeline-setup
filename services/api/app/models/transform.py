from pydantic import BaseModel, Field


class TransformRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    full_refresh: bool = False
