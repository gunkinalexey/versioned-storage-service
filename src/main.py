import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import settings
from database.database import engine, test_db_connection
from database.db_models import Base
from error_handler.error_handler import register_exception_handlers
from error_handler.mappers_registry import error_mapper_registry
from exceptions.mapper import STORAGE_ERROR_STATUS_MAP
from routes.health import router as router_health
from routes.public_ro import router as router_public_ro
from routes.public_rw import router as router_public_rw
from storage.storage import StorageClient

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    os.makedirs("data", exist_ok=True)
    if not await test_db_connection():
        raise RuntimeError("Database connection error")
    if not await StorageClient.test():
        raise RuntimeError("S3 connection error")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    logger.info("Service started")
    yield
    await engine.dispose()
    logger.info("Service stopped")


app = FastAPI(
    title="Versioned Storage Service",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(router_public_rw)
app.include_router(router_public_ro)
app.include_router(router_health)

error_mapper_registry.register_mapper("storage", STORAGE_ERROR_STATUS_MAP)
register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PUBLIC_API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        workers=settings.NUMBER_OF_WORKERS,
    )
