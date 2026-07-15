import logging
import traceback
from datetime import timedelta
from types import TracebackType
from typing import Any, AsyncGenerator, Optional, Self, Type

import httpx
from miniopy_async import Minio

import settings
from exceptions.exceptions import FileDownloadError, FileUploadError

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=f"{settings.S3_HOST}:{settings.S3_PORT}",
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_SECURE,
            region=settings.S3_REGION,
            cert_check=settings.S3_VERIFY_CERTIFICATES,
        )
        self.bucket_name = settings.S3_BUCKET
        self.bucket_region = settings.S3_REGION

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.client.close_session()

    async def get_upload_presigned_url(
        self,
        link: str,
        expires_minutes: float = 5,
    ) -> str:
        return str(
            await self.client.get_presigned_url(
                "PUT",
                bucket_name=self.bucket_name,
                object_name=link,
                expires=timedelta(minutes=expires_minutes),
            )
        )

    async def get_download_presigned_url(
        self,
        link: str,
        expires_minutes: float = 5,
    ) -> str:
        return str(
            await self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=link,
                expires=timedelta(minutes=expires_minutes),
            )
        )

    async def upload_file_by_link(
        self,
        link: str,
        data: Any,
        file_size: int,
    ) -> None:
        url = await self.get_upload_presigned_url(link)
        headers = {"Content-Length": str(file_size)}
        try:
            async with httpx.AsyncClient(
                verify=settings.S3_VERIFY_CERTIFICATES,
            ) as client:
                response = await client.put(url, data=data, headers=headers)
                if not response.is_success:
                    raise FileUploadError(link=link)
        except httpx.RequestError as ex:
            raise FileUploadError(link=link) from ex

    async def download_file_by_link(
        self,
        link: str,
        chunk_size: int = 1024 * 512,
    ) -> AsyncGenerator[bytes, None]:
        url = await self.get_download_presigned_url(link)
        try:
            async with httpx.AsyncClient(
                verify=settings.S3_VERIFY_CERTIFICATES,
            ) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers={"Accept-Encoding": "identity"},
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_raw(chunk_size=chunk_size):
                        yield chunk
        except httpx.HTTPError as ex:
            raise FileDownloadError(link=link) from ex

    async def delete_file_by_link(self, link: str) -> None:
        try:
            await self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=link,
            )
        except Exception as ex:
            logger.error(
                "Failed to delete object '%s': %s\n%s",
                link,
                ex,
                traceback.format_exc(),
            )

    @staticmethod
    async def test() -> bool:
        try:
            async with StorageClient() as storage:
                bucket_exists = await storage.client.bucket_exists(storage.bucket_name)
                if not bucket_exists:
                    await storage.client.make_bucket(
                        bucket_name=storage.bucket_name,
                        location=storage.bucket_region,
                    )
            return True
        except Exception as ex:
            logger.error(
                "S3 connection test failed: %s\n%s",
                ex,
                traceback.format_exc(),
            )
            return False
