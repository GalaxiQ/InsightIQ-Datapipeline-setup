from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import logging

from app.models.base_requests import FetchRequest
from app.core.connection import get_session

router = APIRouter()
logger = logging.getLogger("serve")

@router.post("/fetch")
async def fetch_accounts(req: FetchRequest):
    """
    Fetches account data for a brand from the specified DB.
    """
    async with get_session(req.db_config) as db:
        try:
            res = await db.execute(text("""
            SELECT name, followers, rating, last_updated
            FROM dim_account
            WHERE brand_id = :brand_id
            """), {"brand_id": req.brand_id})
            
            return [dict(r) for r in res]
            
        except Exception as e:
            logger.exception("Fetch failed")
            raise HTTPException(500, f"Query failed: {str(e)}")
