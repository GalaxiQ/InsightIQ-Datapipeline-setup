from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import logging

from app.models.base_requests import BootstrapRequest
from app.core.connection import get_session

router = APIRouter()
logger = logging.getLogger("schema-bootstrap")

@router.post("/bootstrap")
async def bootstrap(req: BootstrapRequest):
    """
    Connects to the DB specified in payload and runs the bootstrap SQL.
    This creates raw_events table.
    """
    async with get_session(req.db_config) as db:
        try:
            with open("sql/bootstrap.sql", "r") as f:
                sql = f.read()

            statements = [s.strip() for s in sql.split(";") if s.strip()]

            for stmt in statements:
                logger.info("Executing schema step")
                await db.execute(text(stmt))

            await db.commit()
            logger.info(f"Schema boostrap complete for db: {req.db_config.db_name}")
            return {"status": "schema ready", "target_db": req.db_config.db_name}

        except Exception as e:
            logger.exception("Schema bootstrap failed")
            raise HTTPException(
                status_code=500, 
                detail=f"Schema bootstrap failed: {str(e)}"
            )
