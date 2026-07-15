from fastapi import APIRouter, Depends, Request

import settings
from database.client_async import AsyncClient
from database.dependencies import get_db_client
from endpoint_handlers.complete_version_endpoint_handler import (
    CompleteVersionEndpointHandler,
)
from endpoint_handlers.create_version_endpoint_handler import (
    CreateVersionEndpointHandler,
)
from endpoint_handlers.set_items_endpoint_handler import SetItemsEndpointHandler
from endpoint_handlers.upload_data_b64_endpoint_handler import (
    UploadDataB64EndpointHandler,
)
from endpoint_handlers.upload_data_endpoint_handler import UploadDataEndpointHandler
from models.schemas.requests import (
    CompleteVersionRequest,
    DataUploadB64Request,
    SetItemsRequest,
    VersionCreateRequest,
)
from models.schemas.responses import (
    CompleteVersionResponse,
    DataUploadB64Response,
    DataUploadResponse,
    SetItemsResponse,
    VersionCreateResponse,
)

router = APIRouter(prefix=settings.PUBLIC_API_PREFIX, tags=["public rw"])


@router.post("/version")
async def create_version(
    request: Request,
    request_data: VersionCreateRequest,
    db_client: AsyncClient = Depends(get_db_client),
) -> VersionCreateResponse:
    endpoint_handler = CreateVersionEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.post("/items")
async def set_items(
    request: Request,
    request_data: SetItemsRequest,
    db_client: AsyncClient = Depends(get_db_client),
) -> SetItemsResponse:
    endpoint_handler = SetItemsEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.post("/data")
async def upload_data(
    request: Request,
    db_client: AsyncClient = Depends(get_db_client),
) -> DataUploadResponse:
    endpoint_handler = UploadDataEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=None,
    )


@router.post("/data_b64")
async def upload_data_b64(
    request: Request,
    request_data: DataUploadB64Request,
    db_client: AsyncClient = Depends(get_db_client),
) -> DataUploadB64Response:
    endpoint_handler = UploadDataB64EndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.post("/version_complete")
async def complete_version(
    request: Request,
    request_data: CompleteVersionRequest,
    db_client: AsyncClient = Depends(get_db_client),
) -> CompleteVersionResponse:
    endpoint_handler = CompleteVersionEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )
