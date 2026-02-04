from pydantic import BaseModel, Field


class SchemaBootstrapRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
