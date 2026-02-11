import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

logger = logging.getLogger("worker-db")

# Master DB Engine
engine = create_async_engine(
    settings.MASTER_DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_master_session():
    async with SessionLocal() as session:
        yield session
