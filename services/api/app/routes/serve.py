from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy import text

from app.core.db import get_db
from app.core.tenant_schema import qualified_table, tenant_schema_name
from app.core.tenant_store import get_tenant_db
from app.core.tenant_db import get_tenant_session

router = APIRouter()

@router.get("/brands/{brand_id}/accounts")
@router.get("/serve/brands/{brand_id}/accounts")
async def get_accounts(
    brand_id: str,
    x_tenant_id: str = Header(...),
    master_db=Depends(get_db)
):
    try:
        cfg = await get_tenant_db(master_db, x_tenant_id)
        dim_account_table = qualified_table(tenant_schema_name(x_tenant_id), "dim_account")
    except Exception:
        raise HTTPException(401, "Invalid tenant")

    async for db in get_tenant_session(cfg):
        res = await db.execute(text(f"""
        SELECT name, followers, rating, last_updated
        FROM {dim_account_table}
        WHERE brand_id = :brand_id
        """), {"brand_id": brand_id})
        return [dict(r._mapping) for r in res]
