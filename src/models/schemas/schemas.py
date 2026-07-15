import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Item(BaseModel):
    uuid: uuid.UUID
    path: str = Field(..., min_length=1, max_length=1000)
    data_hash: str = Field(..., min_length=64, max_length=64)

    @field_validator("data_hash")
    @classmethod
    def validate_data_hash(cls, value: str) -> str:
        normalized = value.lower()
        if any(symbol not in "0123456789abcdef" for symbol in normalized):
            raise ValueError("data_hash must be a SHA-256 hex digest")
        return normalized


class Version(BaseModel):
    collection_uuid: uuid.UUID
    uuid: uuid.UUID
    creation_time: float
    modification_time: float
    version_state: str = "uploading_items"
    name: str
    description: Optional[str]
