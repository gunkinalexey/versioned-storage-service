import logging
import traceback

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.SERVICE_DB_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def test_db_connection() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception as ex:
        logger.error(
            "Database connection test failed: %s\n%s",
            ex,
            traceback.format_exc(),
        )
        return False
