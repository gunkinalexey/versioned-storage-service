import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any, Optional

from fastapi import Request, Response

from database.client_async import AsyncClient
from models.schemas.base import BaseRequest, BaseResponse

logger = logging.getLogger(__name__)


class BaseEndpointHandler(ABC):
    @abstractmethod
    async def process_request(
        self,
        db_client: AsyncClient,
        request_data: BaseRequest,
        **kwargs: Any,
    ) -> BaseResponse | Response:
        pass

    @abstractmethod
    def get_log_message(
        self,
        request_data: BaseRequest,
        response_data: BaseResponse | Response,
    ) -> str:
        pass

    async def preprocess_request(
        self,
        request: Request,
        request_data: Optional[BaseRequest] = None,
        **kwargs: Any,
    ) -> tuple[Optional[BaseRequest], dict[str, Any]]:
        return request_data, kwargs

    async def handle_request(
        self,
        request: Request,
        db_client: AsyncClient,
        request_data: Optional[BaseRequest] = None,
    ) -> BaseResponse | Response:
        try:
            processed_request_data, kwargs = await self.preprocess_request(
                request,
                request_data,
            )
            if processed_request_data is None:
                raise ValueError("Request data was not prepared")

            response = await self.process_request(
                db_client,
                processed_request_data,
                **kwargs,
            )
            logger.info(
                "%s method=%s path=%s",
                self.get_log_message(processed_request_data, response),
                request.method,
                request.url.path,
            )
            return response
        except Exception as ex:
            logger.error(
                "Endpoint failed: method=%s path=%s error=%s traceback=%s",
                request.method,
                request.url.path,
                ex,
                traceback.format_exc(),
            )
            raise
