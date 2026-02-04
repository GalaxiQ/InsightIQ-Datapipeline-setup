import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from app.models.base_requests import DBConfig

logger = logging.getLogger("db-connector")

_POOLS = {}

def make_url(cfg: DBConfig):
    return (
        f"postgresql+asyncpg://{cfg.user}:{cfg.password}"
        f"@{cfg.host}:{cfg.port}/{cfg.db_name}"
    )

def get_engine(cfg: DBConfig):
    # Cache key based on connection details
    key = f"{cfg.host}:{cfg.port}:{cfg.db_name}:{cfg.user}"
    
    if key not in _POOLS:
        logger.info(f"Creating new pool for {key}")
        _POOLS[key] = create_async_engine(
            make_url(cfg),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
    return _POOLS[key]

@asynccontextmanager
async def get_session(cfg: DBConfig):
    """Provide a transactional scope around a series of operations."""
    engine = get_engine(cfg)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        try:
            yield session
        except Exception:
            logger.exception("Database session error")
            await session.rollback()
            raise
        finally:
            await session.close()
