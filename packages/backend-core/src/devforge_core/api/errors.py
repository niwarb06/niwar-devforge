from collections.abc import Mapping

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
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = dict(headers or {})


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiError):
        raise exc
    payload = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
        headers=exc.headers,
    )


def not_authenticated() -> ApiError:
    return ApiError(status_code=401, code="not_authenticated")


def invalid_credentials() -> ApiError:
    return ApiError(status_code=401, code="invalid_credentials")


def registration_failed() -> ApiError:
    return ApiError(status_code=400, code="registration_failed")


def password_policy_violation(reason: str) -> ApiError:
    return ApiError(status_code=422, code="password_policy_violation", message=reason)


def rate_limited(retry_after_seconds: int) -> ApiError:
    return ApiError(
        status_code=429,
        code="rate_limited",
        headers={"Retry-After": str(max(1, retry_after_seconds))},
    )


def temporarily_unavailable() -> ApiError:
    return ApiError(status_code=503, code="temporarily_unavailable")


def permission_denied() -> ApiError:
    return ApiError(status_code=403, code="permission_denied")


def resource_not_found() -> ApiError:
    return ApiError(status_code=404, code="resource_not_found")
