from fastapi import APIRouter

import settings
from models.schemas.responses import HealthCheckResponse

router = APIRouter(prefix=settings.PUBLIC_API_PREFIX, tags=["health"])


@router.get("/health")
async def healthcheck() -> HealthCheckResponse:
    return HealthCheckResponse()
