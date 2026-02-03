from pydantic import BaseModel, Field

class TenantRegisterRequest(BaseModel):
    org_name: str = Field(..., min_length=3)
    host: str
    port: int = 5432
    db_name: str
    user: str
    password: str
