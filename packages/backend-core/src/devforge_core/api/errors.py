from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse

from .contracts import ErrorResponse


@dataclass(frozen=True, slots=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str | None = None


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    payload = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


def not_authenticated() -> ApiError:
    return ApiError(status_code=401, code="not_authenticated")


def permission_denied() -> ApiError:
    return ApiError(status_code=403, code="permission_denied")


def resource_not_found() -> ApiError:
    return ApiError(status_code=404, code="resource_not_found")
