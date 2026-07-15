from typing import AsyncGenerator

from fastapi.responses import StreamingResponse

from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import DownloadDataRequest
from storage.storage import StorageClient


class DownloadDataEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: DownloadDataRequest,
        **kwargs: object,
    ) -> StreamingResponse:
        link = await db_client.get_data_link(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
        )

        async def file_stream() -> AsyncGenerator[bytes, None]:
            async with StorageClient() as storage:
                async for chunk in storage.download_file_by_link(link=link):
                    yield chunk

        return StreamingResponse(
            file_stream(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{request_data.item_uuid}"; '
                    f"filename*=UTF-8''{request_data.item_uuid}"
                ),
            },
        )

    def get_log_message(
        self,
        request_data: DownloadDataRequest,
        response_data: StreamingResponse,
    ) -> str:
        return f"Downloaded data stream for item {request_data.item_uuid}"
