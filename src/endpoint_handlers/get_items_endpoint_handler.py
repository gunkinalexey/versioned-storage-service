from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import GetItemsRequest
from models.schemas.responses import GetItemsResponse, ListItems


class GetItemsEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: GetItemsRequest,
    ) -> GetItemsResponse:
        items = await db_client.get_items(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
        )
        return GetItemsResponse(data=ListItems(items=items))

    def get_log_message(
        self,
        request_data: GetItemsRequest,
        response_data: GetItemsResponse,
    ) -> str:
        return f"Received {len(response_data.data.items)} items"
