import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logger = logging.getLogger("worker-tenant")

async def get_all_tenants(master_session):
    """
    Fetches all active tenant details by scanning schemas starting with 'org_'.
    Since all tenants share the same remote database, the host/user etc are the same.
    """
    try:
        # Scan information_schema for schemas starting with 'org_'
        query = text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'org_%'
        """)
        result = await master_session.execute(query)
        schemas = [row.schema_name for row in result.fetchall()]
        
        # We need to return the full config for each tenant
        # Since they are all in the same DB, we use the master connection info
        # The user provided these Production credentials:
        # Host: 66.135.22.167 Port: 5432 Username: postgres Password: galaxiq
        
        return [
            {
                "tenant_id": s,
                "host": "66.135.22.167",
                "port": 5432,
                "db_name": "galaxiq_tenants",
                "user": "postgres",
                "password": "galaxiq"
            }
            for s in schemas
        ]
    except Exception:
        logger.exception("Failed to fetch tenants from schemas")
        return []

_POOLS = {}

def get_engine(cfg):
    url = f"postgresql+asyncpg://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['db_name']}"
    key = f"{cfg['host']}:{cfg['port']}:{cfg['db_name']}"
    if key not in _POOLS:
        _POOLS[key] = create_async_engine(url, pool_size=5, max_overflow=10)
    return _POOLS[key]

async def get_tenant_session(cfg: dict):
    """
    Yields a session configured for the specific tenant's DB and schema.
    """
    tenant_id = cfg["tenant_id"]
    schema_name = tenant_id.strip().lower() # Use tenant_id directly as schema name
    
    engine = get_engine(cfg)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            # We must use the qualified names in queries too, but search_path is a good safety net
            await session.execute(text(f'SET search_path TO "{schema_name}", public'))
            yield session
        except Exception:
            logger.exception(f"Error in tenant session for {tenant_id}")
            raise
        finally:
            await session.close()
