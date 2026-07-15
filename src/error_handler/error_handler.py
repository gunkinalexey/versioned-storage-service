import json
import logging
import traceback
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from error_handler.resolver import resolve_error_response

logger = logging.getLogger(__name__)


async def _safe_request_body(request: Request) -> Optional[str]:
    try:
        body = await request.body()
        if not body:
            return None

        try:
            parsed = json.loads(body.decode("utf-8"))
            return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            return str(body.decode("utf-8", errors="replace"))
    except Exception:
        return None


async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    status_code, message, data = resolve_error_response(exc)
    response_body = {
        "result": "Error",
        "message": message,
        "data": data,
    }

    logger.error(
        "Request failed: method=%s path=%s error=%s traceback=%s body=%s",
        request.method,
        request.url.path,
        str(exc),
        traceback.format_exc(),
        await _safe_request_body(request),
    )

    return JSONResponse(status_code=status_code, content=response_body)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, global_exception_handler)
