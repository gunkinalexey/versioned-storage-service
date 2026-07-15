from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

import settings
from database.client_async import AsyncClient
from database.dependencies import get_db_client
from endpoint_handlers.download_data_b64_endpoint_handler import (
    DownloadDataB64EndpointHandler,
)
from endpoint_handlers.download_data_endpoint_handler import (
    DownloadDataEndpointHandler,
)
from endpoint_handlers.get_collections_endpoint_handler import (
    GetCollectionsEndpointHandler,
)
from endpoint_handlers.get_items_endpoint_handler import GetItemsEndpointHandler
from models.schemas.requests import (
    DownloadDataB64Request,
    DownloadDataRequest,
    GetCollectionsRequest,
    GetItemsRequest,
)
from models.schemas.responses import (
    DownloadDataB64Response,
    GetCollectionsResponse,
    GetItemsResponse,
)

router = APIRouter(prefix=settings.PUBLIC_API_PREFIX, tags=["public ro"])


@router.get("/collection_list")
async def get_collection_list(
    request: Request,
    request_data: GetCollectionsRequest = Depends(),
    db_client: AsyncClient = Depends(get_db_client),
) -> GetCollectionsResponse:
    endpoint_handler = GetCollectionsEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.get("/items")
async def get_items(
    request: Request,
    request_data: GetItemsRequest = Depends(),
    db_client: AsyncClient = Depends(get_db_client),
) -> GetItemsResponse:
    endpoint_handler = GetItemsEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.get("/data", response_class=StreamingResponse)
async def download_data(
    request: Request,
    request_data: DownloadDataRequest = Depends(),
    db_client: AsyncClient = Depends(get_db_client),
) -> StreamingResponse:
    endpoint_handler = DownloadDataEndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )


@router.get("/data_b64")
async def download_data_b64(
    request: Request,
    request_data: DownloadDataB64Request = Depends(),
    db_client: AsyncClient = Depends(get_db_client),
) -> DownloadDataB64Response:
    endpoint_handler = DownloadDataB64EndpointHandler()
    return await endpoint_handler.handle_request(
        request=request,
        db_client=db_client,
        request_data=request_data,
    )
