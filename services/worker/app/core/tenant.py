import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logger = logging.getLogger("worker-tenant")

async def get_all_tenants(master_session):
    """
    Fetches all active tenant details from the registry.
    """
    try:
        query = text("SELECT tenant_id, host, port, db_name, db_user, db_password FROM tenants")
        result = await master_session.execute(query)
        return [
            {
                "tenant_id": row.tenant_id,
                "host": row.host,
                "port": row.port,
                "db_name": row.db_name,
                "user": row.db_user,
                "password": row.db_password
            }
            for row in result.fetchall()
        ]
    except Exception:
        logger.exception("Failed to fetch tenants")
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
    safe_id = tenant_id.strip().lower().replace('-', '_')
    schema_name = f"tenant_{safe_id}"
    
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
