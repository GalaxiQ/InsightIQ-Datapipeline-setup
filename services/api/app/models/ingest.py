from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class IngestRequest(BaseModel):
    brand_id: str = Field(..., description="Brand or tenant identifier")
    platform: Optional[str] = Field(None, description="facebook, instagram, twitter, etc")
    payload: Dict[str, Any] = Field(..., description="Raw JSON payload")
    schema_version: Optional[str] = Field("v1")
