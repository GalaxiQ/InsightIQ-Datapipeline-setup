import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("tenant-db")

_POOLS = {}

def make_url(cfg):
    return (
        f"postgresql+asyncpg://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['db_name']}"
    )

def get_engine(cfg):
    key = f"{cfg['host']}:{cfg['port']}:{cfg['db_name']}"
    if key not in _POOLS:
        logger.info("Creating pool", extra={"db": key})
        _POOLS[key] = create_async_engine(
            make_url(cfg),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    return _POOLS[key]

async def get_tenant_session(cfg):
    engine = get_engine(cfg)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        try:
            yield session
        except Exception:
            logger.exception("Tenant DB error")
            raise
