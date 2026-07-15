import base64
import hashlib

from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from exceptions.exceptions import DataHashError, InvalidDataFormatError
from models.schemas.requests import DataUploadB64Request
from models.schemas.responses import DataUploadB64Response
from storage.storage import StorageClient


class UploadDataB64EndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: DataUploadB64Request,
    ) -> DataUploadB64Response:
        try:
            data = base64.b64decode(request_data.data, validate=True)
        except ValueError as ex:
            raise InvalidDataFormatError() from ex

        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != request_data.data_hash:
            raise DataHashError(request_data.data_hash, actual_hash)

        link = await db_client.validate_upload_and_get_link(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
            data_hash=actual_hash,
        )
        async with StorageClient() as storage:
            await storage.upload_file_by_link(
                link=link,
                data=data,
                file_size=len(data),
            )
        await db_client.complete_file_upload(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
        )
        return DataUploadB64Response()

    def get_log_message(
        self,
        request_data: DataUploadB64Request,
        response_data: DataUploadB64Response,
    ) -> str:
        return f"Uploaded data for item {request_data.item_uuid}"
