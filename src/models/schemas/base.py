from typing import Optional

from pydantic import BaseModel, Field


class BaseRequest(BaseModel):
    pass


class BaseResponse(BaseModel):
    result: str
    message: str
    data: Optional[dict] = Field(default_factory=dict)
