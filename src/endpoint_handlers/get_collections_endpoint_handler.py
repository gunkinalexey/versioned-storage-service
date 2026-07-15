from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import GetCollectionsRequest
from models.schemas.responses import GetCollectionsResponse, ResponseCollections


class GetCollectionsEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: GetCollectionsRequest,
    ) -> GetCollectionsResponse:
        collections = await db_client.get_collections(request_data.name_filter)
        return GetCollectionsResponse(
            data=ResponseCollections(collections=collections)
        )

    def get_log_message(
        self,
        request_data: GetCollectionsRequest,
        response_data: GetCollectionsResponse,
    ) -> str:
        return f"Received {len(response_data.data.collections)} collections"
