from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy import text
import logging

from app.core.db import get_db
from app.core.tenant_store import get_tenant_db
from app.core.tenant_db import get_tenant_session

router = APIRouter()
logger = logging.getLogger("schema-bootstrap")


@router.post("/bootstrap")
async def bootstrap(
    x_tenant_id: str = Header(...),
    master_db=Depends(get_db)
):
    # -------------------------
    # Resolve tenant config
    # -------------------------
    try:
        cfg = await get_tenant_db(master_db, x_tenant_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid tenant")

    # -------------------------
    # Execute bootstrap safely
    # -------------------------
    async for db in get_tenant_session(cfg):
        try:
            with open("sql/bootstrap.sql", "r") as f:
                sql = f.read()

            statements = [s.strip() for s in sql.split(";") if s.strip()]

            for stmt in statements:
                logger.info("Executing schema step")
                await db.execute(text(stmt))

            await db.commit()
            logger.info("Tenant schema bootstrap complete")

        except Exception as e:
            await db.rollback()
            logger.exception("Schema bootstrap failed")
            raise HTTPException(
                status_code=500,
                detail=f"Schema bootstrap failed: {str(e)}"
            )

    return {"status": "schema ready"}
