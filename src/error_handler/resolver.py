from typing import Any

from fastapi import HTTPException

from error_handler.base_exception import BaseError
from error_handler.mappers_registry import error_mapper_registry


def resolve_error_response(exc: Exception) -> tuple[int, str, dict[str, Any]]:
    if isinstance(exc, BaseError):
        status_code = error_mapper_registry.resolve_status_code(
            exc,
            default_status_code=500,
        )
        data = dict(exc.extra or {})
        data.setdefault("error_type", exc.error_type)
        return status_code, str(exc), data

    if isinstance(exc, HTTPException):
        if isinstance(exc.detail, dict):
            detail = dict(exc.detail)
            message = str(detail.get("message", "HTTP Error"))
            data = detail.get("data", {})
            if not isinstance(data, dict):
                data = {"raw_data": data}
            data.setdefault("error_type", "HTTPException")
            return exc.status_code, message, data

        return exc.status_code, str(exc.detail), {"error_type": "HTTPException"}

    return 500, "Internal Server Error", {"error_type": "InternalServerError"}
