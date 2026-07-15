import base64

from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import DownloadDataB64Request
from models.schemas.responses import DownloadDataB64Response
from storage.storage import StorageClient


class DownloadDataB64EndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: DownloadDataB64Request,
    ) -> DownloadDataB64Response:
        link = await db_client.get_data_link(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
        )
        data = b""
        async with StorageClient() as storage:
            async for chunk in storage.download_file_by_link(link=link):
                data += chunk
        return DownloadDataB64Response(data=base64.b64encode(data).decode("utf-8"))

    def get_log_message(
        self,
        request_data: DownloadDataB64Request,
        response_data: DownloadDataB64Response,
    ) -> str:
        return f"Downloaded data for item {request_data.item_uuid}"
