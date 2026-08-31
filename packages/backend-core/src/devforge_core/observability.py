import json
import logging
import re
from collections.abc import Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_DEVFORGE_HANDLER_MARKER = "_devforge_json_handler"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    resolved_level = level.upper()
    logger = logging.getLogger("devforge")
    logger.setLevel(resolved_level)
    logger.propagate = False

    for existing in logger.handlers:
        if getattr(existing, _DEVFORGE_HANDLER_MARKER, False):
            existing.setLevel(resolved_level)
            existing.setFormatter(JsonFormatter())
            return

    handler = logging.StreamHandler()
    handler.setLevel(resolved_level)
    handler.setFormatter(JsonFormatter())
    setattr(handler, _DEVFORGE_HANDLER_MARKER, True)
    logger.addHandler(handler)


def _resolve_request_id(candidate: str | None) -> str:
    if candidate is not None and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        logger_factory: Callable[[], logging.Logger] | None = None,
    ) -> None:
        super().__init__(app)
        self._logger_factory = logger_factory or (lambda: logging.getLogger("devforge.request"))

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _resolve_request_id(request.headers.get("X-Request-ID"))
        started = perf_counter()
        response = await call_next(request)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        self._logger_factory().info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
