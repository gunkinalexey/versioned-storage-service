import uuid
from typing import List, Optional

from pydantic import Field, field_validator

from models.schemas.base import BaseRequest
from models.schemas.schemas import Item


class VersionCreateRequest(BaseRequest):
    collection_uuid: uuid.UUID
    name: str = Field(..., min_length=1, max_length=250)
    description: Optional[str] = Field(default="", max_length=5000)


class SetItemsRequest(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    items: List[Item] = Field(..., min_length=1)


class DataUploadRequest(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    item_uuid: uuid.UUID
    file_size: int = Field(..., gt=0)
    data_hash: str = Field(..., min_length=64, max_length=64)

    @field_validator("data_hash")
    @classmethod
    def validate_data_hash(cls, value: str) -> str:
        normalized = value.lower()
        if any(symbol not in "0123456789abcdef" for symbol in normalized):
            raise ValueError("data_hash must be a SHA-256 hex digest")
        return normalized


class DataUploadB64Request(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    item_uuid: uuid.UUID
    data_hash: str = Field(..., min_length=64, max_length=64)
    data: str = Field(..., min_length=1)

    @field_validator("data_hash")
    @classmethod
    def validate_data_hash(cls, value: str) -> str:
        normalized = value.lower()
        if any(symbol not in "0123456789abcdef" for symbol in normalized):
            raise ValueError("data_hash must be a SHA-256 hex digest")
        return normalized


class CompleteVersionRequest(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID


class GetCollectionsRequest(BaseRequest):
    name_filter: str = ""


class GetItemsRequest(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID


class DownloadDataRequest(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    item_uuid: uuid.UUID


class DownloadDataB64Request(BaseRequest):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    item_uuid: uuid.UUID
