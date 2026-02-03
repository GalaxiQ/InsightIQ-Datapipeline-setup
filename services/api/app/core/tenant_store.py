import uuid
import logging
from sqlalchemy import text

logger = logging.getLogger("tenant-store")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
  tenant_id TEXT PRIMARY KEY,
  org_name TEXT,
  host TEXT,
  port INT,
  db_name TEXT,
  db_user TEXT,
  db_password TEXT,
  created_at TIMESTAMP DEFAULT now()
);
"""

INSERT_SQL = """
INSERT INTO tenants
(tenant_id, org_name, host, port, db_name, db_user, db_password)
VALUES
(:tenant_id, :org_name, :host, :port, :db_name, :db_user, :db_password)
"""

GET_SQL = """
SELECT host, port, db_name, db_user, db_password
FROM tenants
WHERE tenant_id = :tenant_id
"""

async def ensure_registry(db):
    await db.execute(text(CREATE_SQL))
    await db.commit()

async def register_tenant(db, org_name, host, port, db_name, user, password):
    tenant_id = str(uuid.uuid4())

    await db.execute(text(INSERT_SQL), {
        "tenant_id": tenant_id,
        "org_name": org_name,
        "host": host,
        "port": port,
        "db_name": db_name,
        "db_user": user,
        "db_password": password
    })
    await db.commit()

    logger.info("Tenant registered", extra={"tenant_id": tenant_id})
    return tenant_id

async def get_tenant_db(db, tenant_id):
    res = await db.execute(text(GET_SQL), {"tenant_id": tenant_id})
    row = res.fetchone()

    if not row:
        raise ValueError("Tenant not found")

    return {
        "host": row.host,
        "port": row.port,
        "db_name": row.db_name,
        "user": row.db_user,
        "password": row.db_password
    }
