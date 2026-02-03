from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import TenantRegisterRequest
from app.core.db import get_db
from app.core.tenant_store import ensure_registry, register_tenant

router = APIRouter()

@router.post("/register")
async def register(req: TenantRegisterRequest, db: AsyncSession = Depends(get_db)):
    await ensure_registry(db)
    tenant_id = await register_tenant(
        db, req.org_name, req.host, req.port,
        req.db_name, req.user, req.password
    )
    return {"tenant_id": tenant_id}
