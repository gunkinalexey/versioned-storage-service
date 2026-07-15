import uuid
from typing import List, Optional

from pydantic import BaseModel

from models.schemas.base import BaseResponse
from models.schemas.schemas import Item


class CollectionAndVersionUUID(BaseModel):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID


class VersionCreateResponse(BaseResponse):
    result: str = "Success"
    message: str = "Version created successfully"
    data: CollectionAndVersionUUID


class ResponseItemsData(BaseModel):
    items_data_to_upload: List[uuid.UUID]


class SetItemsResponse(BaseResponse):
    result: str = "Success"
    message: str = "Items set successfully"
    data: ResponseItemsData


class DataUploadResponse(BaseResponse):
    result: str = "Success"
    message: str = "Item data uploaded successfully"


class DataUploadB64Response(BaseResponse):
    result: str = "Success"
    message: str = "Item data uploaded successfully"


class CompleteVersionResponse(BaseResponse):
    result: str = "Success"
    message: str = "Version completed successfully"


class CollectionVersion(BaseModel):
    collection_uuid: uuid.UUID
    version_uuid: uuid.UUID
    name: str
    description: Optional[str]
    creation_time: float
    modification_time: float


class ResponseCollections(BaseModel):
    collections: List[CollectionVersion]


class GetCollectionsResponse(BaseResponse):
    result: str = "Success"
    message: str = "Collection list received successfully"
    data: ResponseCollections


class ListItems(BaseModel):
    items: List[Item]


class GetItemsResponse(BaseResponse):
    result: str = "Success"
    message: str = "Items received successfully"
    data: ListItems


class DownloadDataB64Response(BaseResponse):
    result: str = "Success"
    message: str = "Item data downloaded successfully"
    data: str


class HealthCheckResponse(BaseResponse):
    result: str = "Success"
    message: str = "Checked successfully"
