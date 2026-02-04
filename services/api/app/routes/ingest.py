import json
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import logging

from app.models.base_requests import IngestRequest
from app.core.connection import get_session
from app.utils.hash import hash_payload

router = APIRouter()
logger = logging.getLogger("ingest")

SQL = """
INSERT INTO raw_events
(brand_id, domain, platform, raw_json, schema_version, payload_hash)
VALUES
(:brand_id, :domain, :platform, CAST(:payload AS jsonb), :schema_version, :hash)
"""

@router.post("/{domain}")
async def ingest(domain: str, req: IngestRequest):
    """
    Ingests data into the raw_events table of the specified DB.
    """
    # Serialize JSON ONCE, deterministically
    payload_str = json.dumps(req.payload, sort_keys=True)
    payload_hash = hash_payload(payload_str)

    async with get_session(req.db_config) as db:
        try:
            await db.execute(
                text(SQL),
                {
                    "brand_id": req.brand_id,
                    "domain": domain,
                    "platform": req.platform,
                    "payload": payload_str,
                    "schema_version": req.schema_version,
                    "hash": payload_hash,
                },
            )
            await db.commit()
            return {"status": "ingested", "hash": payload_hash}
            
        except Exception as e:
            logger.exception("Ingestion failed")
            raise HTTPException(500, f"Ingestion failed: {str(e)}")
