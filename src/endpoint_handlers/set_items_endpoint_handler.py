from database.client_async import AsyncClient
from endpoint_handlers.base_endpoint_handler import BaseEndpointHandler
from models.schemas.requests import SetItemsRequest
from models.schemas.responses import ResponseItemsData, SetItemsResponse


class SetItemsEndpointHandler(BaseEndpointHandler):
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: SetItemsRequest,
    ) -> SetItemsResponse:
        item_uuids = await db_client.insert_items(
            collection_uuid=request_data.collection_uuid,
            version_uuid=request_data.version_uuid,
            items=request_data.items,
        )
        return SetItemsResponse(
            data=ResponseItemsData(items_data_to_upload=item_uuids)
        )

    def get_log_message(
        self,
        request_data: SetItemsRequest,
        response_data: SetItemsResponse,
    ) -> str:
        return (
            f"Set {len(request_data.items)} items for version "
            f"{request_data.version_uuid}"
        )
