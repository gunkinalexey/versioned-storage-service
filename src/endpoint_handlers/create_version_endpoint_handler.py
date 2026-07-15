import datetime
import uuid

from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import VersionCreateRequest
from models.schemas.responses import (
    CollectionAndVersionUUID,
    VersionCreateResponse,
)
from models.schemas.schemas import Version


class CreateVersionEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: VersionCreateRequest,
    ) -> VersionCreateResponse:
        current_timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        version = Version(
            collection_uuid=request_data.collection_uuid,
            uuid=uuid.uuid4(),
            creation_time=current_timestamp,
            modification_time=current_timestamp,
            version_state="uploading_items",
            name=request_data.name,
            description=request_data.description,
        )
        await db_client.create_version(version)
        return VersionCreateResponse(
            data=CollectionAndVersionUUID(
                collection_uuid=version.collection_uuid,
                version_uuid=version.uuid,
            )
        )

    def get_log_message(
        self,
        request_data: VersionCreateRequest,
        response_data: VersionCreateResponse,
    ) -> str:
        return (
            f"Created version {response_data.data.version_uuid} "
            f"for collection {response_data.data.collection_uuid}"
        )
