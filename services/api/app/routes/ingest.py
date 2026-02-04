import json
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy import text

from app.models.ingest import IngestRequest
from app.core.db import get_db
from app.core.tenant_schema import qualified_table, tenant_schema_name
from app.core.tenant_store import get_tenant_db
from app.core.tenant_db import get_tenant_session
from app.utils.hash import hash_payload

router = APIRouter()

@router.post("/{domain}")
async def ingest(
    domain: str,
    req: IngestRequest,
    x_tenant_id: str = Header(...),
    master_db=Depends(get_db)
):
    try:
        cfg = await get_tenant_db(master_db, x_tenant_id)
        raw_events_table = qualified_table(tenant_schema_name(x_tenant_id), "raw_events")
    except Exception:
        raise HTTPException(401, "Invalid tenant")

    sql = f"""
    INSERT INTO {raw_events_table}
    (brand_id, domain, platform, raw_json, schema_version, payload_hash)
    VALUES
    (:brand_id, :domain, :platform, CAST(:payload AS jsonb), :schema_version, :hash)
    """

    # Serialize JSON ONCE, deterministically
    payload_str = json.dumps(req.payload, sort_keys=True)

    async for db in get_tenant_session(cfg):
        try:
            await db.execute(
                text(sql),
                {
                    "brand_id": req.brand_id,
                    "domain": domain,
                    "platform": req.platform,
                    "payload": payload_str,
                    "schema_version": req.schema_version,
                    "hash": hash_payload(payload_str),
                },
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(500, "Ingestion failed")

    return {"status": "ingested"}
