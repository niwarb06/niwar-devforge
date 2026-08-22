from fastapi import Request
from fastapi.responses import JSONResponse

from .contracts import ErrorResponse


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiError):
        raise exc
    payload = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


def not_authenticated() -> ApiError:
    return ApiError(status_code=401, code="not_authenticated")


def permission_denied() -> ApiError:
    return ApiError(status_code=403, code="permission_denied")


def resource_not_found() -> ApiError:
    return ApiError(status_code=404, code="resource_not_found")
