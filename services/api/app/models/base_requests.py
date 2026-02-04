from pydantic import BaseModel
from typing import Optional, Dict

class DBConfig(BaseModel):
    host: str
    port: int
    db_name: str
    user: str
    password: str

class BootstrapRequest(BaseModel):
    db_config: DBConfig

class IngestRequest(BaseModel):
    db_config: DBConfig
    brand_id: str
    platform: str
    schema_version: str = "v1"
    payload: Dict

class FetchRequest(BaseModel):
    db_config: DBConfig
    brand_id: str
