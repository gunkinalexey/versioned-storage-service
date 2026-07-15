import hashlib
import uuid
from typing import Any, AsyncGenerator

from fastapi import HTTPException, Request

from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from exceptions.exceptions import DataHashError
from models.schemas.requests import DataUploadRequest
from models.schemas.responses import DataUploadResponse
from storage.storage import StorageClient


class UploadDataEndpointHandler(BaseEndpointHandler):
    async def preprocess_request(
        self,
        request: Request,
        request_data: DataUploadRequest | None = None,
        **kwargs: Any,
    ) -> tuple[DataUploadRequest, dict[str, Any]]:
        content_length = request.headers.get("Content-Length")
        if content_length is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required header: Content-Length",
            )

        data_hash = request.headers.get("X-File-Hash")
        if data_hash is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required header: X-File-Hash",
            )

        collection_uuid = request.headers.get("X-Collection-UUID")
        if collection_uuid is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required header: X-Collection-UUID",
            )

        version_uuid = request.headers.get("X-Version-UUID")
        if version_uuid is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required header: X-Version-UUID",
            )

        item_uuid = request.headers.get("X-Item-UUID")
        if item_uuid is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required header: X-Item-UUID",
            )

        prepared_request = DataUploadRequest(
            collection_uuid=uuid.UUID(collection_uuid),
            version_uuid=uuid.UUID(version_uuid),
            item_uuid=uuid.UUID(item_uuid),
            file_size=int(content_length),
            data_hash=data_hash,
        )
        kwargs["request_stream"] = request.stream()
        return prepared_request, kwargs

    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: DataUploadRequest,
        **kwargs: Any,
    ) -> DataUploadResponse:
        link = await db_client.validate_upload_and_get_link(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
            data_hash=request_data.data_hash,
        )

        hash_calculator = hashlib.sha256()
        request_stream = kwargs["request_stream"]

        async def stream_with_hash() -> AsyncGenerator[bytes, None]:
            async for chunk in request_stream:
                hash_calculator.update(chunk)
                yield chunk

        async with StorageClient() as storage:
            await storage.upload_file_by_link(
                link=link,
                data=stream_with_hash(),
                file_size=request_data.file_size,
            )
            actual_hash = hash_calculator.hexdigest()
            if actual_hash != request_data.data_hash:
                await storage.delete_file_by_link(link)
                raise DataHashError(request_data.data_hash, actual_hash)

        await db_client.complete_file_upload(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            item_uuid=request_data.item_uuid,
        )
        return DataUploadResponse()

    def get_log_message(
        self,
        request_data: DataUploadRequest,
        response_data: DataUploadResponse,
    ) -> str:
        return f"Uploaded data stream for item {request_data.item_uuid}"
