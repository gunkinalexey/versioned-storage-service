from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import CompleteVersionRequest
from models.schemas.responses import CompleteVersionResponse


class CompleteVersionEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: CompleteVersionRequest,
    ) -> CompleteVersionResponse:
        await db_client.complete_version(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
        )
        return CompleteVersionResponse()

    def get_log_message(
        self,
        request_data: CompleteVersionRequest,
        response_data: CompleteVersionResponse,
    ) -> str:
        return f"Completed version {request_data.version_uuid}"
