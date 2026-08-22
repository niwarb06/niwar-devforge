from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from devforge_core.auth.abuse import (
    RateLimitBackendUnavailable,
    RateLimiter,
    RedisFixedWindowRateLimiter,
)
from devforge_core.auth.contracts import Actor, LoginCommand, RegisterCommand
from devforge_core.auth.errors import (
    EmailAlreadyExists,
    InvalidCredentials,
    PasswordPolicyViolation,
)
from devforge_core.auth.repository import SqlAlchemyUserRepository
from devforge_core.auth.security import Argon2Hasher
from devforge_core.auth.service import AuthService
from devforge_core.auth.sessions import DatabaseSessionIssuer
from devforge_core.cache import get_redis
from devforge_core.config import Settings, get_settings
from devforge_core.database import get_db

from .contracts import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    RegistrationAcceptedResponse,
    SessionTokenResponse,
)
from .errors import (
    auth_service_unavailable,
    invalid_credentials,
    not_authenticated,
    password_policy_violation,
    rate_limited,
)

_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="DevForgeSession",
    description=(
        "Opaque DevForge session token for mobile/API transports. "
        "Browser JavaScript must use the server-mediated BFF/cookie transport instead."
    ),
)

_LOGIN_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}
_REGISTER_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    actor: Actor
    raw_token: str


def get_rate_limiter(
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> RateLimiter:
    return RedisFixedWindowRateLimiter(redis_client)


async def get_authenticated_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthenticatedSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise not_authenticated()

    actor = await DatabaseSessionIssuer(db).resolve(credentials.credentials)
    if actor is None:
        raise not_authenticated()

    return AuthenticatedSession(actor=actor, raw_token=credentials.credentials)


async def get_current_actor(
    session: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
) -> Actor:
    return session.actor


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegistrationAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses=_REGISTER_RESPONSES,
)
async def register_credentials(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RegistrationAcceptedResponse:
    source = _credential_source(request, settings)
    _enforce_limit(
        limiter,
        scope="auth:register:source",
        subject=source,
        limit=settings.auth_register_source_limit,
        window_seconds=settings.auth_register_window_seconds,
    )
    _enforce_limit(
        limiter,
        scope="auth:register:identifier",
        subject=payload.email,
        limit=settings.auth_register_identifier_limit,
        window_seconds=settings.auth_register_window_seconds,
    )

    display_name = payload.display_name
    if display_name is not None:
        display_name = display_name.strip() or None

    service = _auth_service(db, settings)
    command = RegisterCommand(
        email=payload.email.strip().lower(),
        password=payload.password,
        display_name=display_name,
    )

    try:
        await service.register(command)
    except EmailAlreadyExists:
        # Deliberately return the same response as a new registration.
        pass
    except PasswordPolicyViolation as exc:
        raise password_policy_violation(exc.reason) from exc

    response.headers["Cache-Control"] = "no-store"
    return RegistrationAcceptedResponse()


@router.post(
    "/login",
    response_model=SessionTokenResponse,
    responses=_LOGIN_RESPONSES,
)
async def login_credentials(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionTokenResponse:
    source = _credential_source(request, settings)
    _enforce_limit(
        limiter,
        scope="auth:login:source",
        subject=source,
        limit=settings.auth_login_source_limit,
        window_seconds=settings.auth_login_window_seconds,
    )
    _enforce_limit(
        limiter,
        scope="auth:login:identifier",
        subject=payload.identifier,
        limit=settings.auth_login_identifier_limit,
        window_seconds=settings.auth_login_window_seconds,
    )

    service = _auth_service(db, settings)
    try:
        _actor, raw_token = await service.login(
            LoginCommand(
                identifier=payload.identifier,
                password=payload.password,
            )
        )
    except InvalidCredentials as exc:
        raise invalid_credentials() from exc

    response.headers["Cache-Control"] = "no-store"
    return SessionTokenResponse(
        session_token=raw_token,
        expires_in_seconds=settings.session_ttl_minutes * 60,
    )


@router.delete(
    "/session",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}},
)
async def revoke_current_session(
    session: Annotated[AuthenticatedSession, Depends(get_authenticated_session)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    await DatabaseSessionIssuer(db).revoke(session.raw_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _auth_service(db: Session, settings: Settings) -> AuthService:
    return AuthService(
        users=SqlAlchemyUserRepository(db),
        passwords=Argon2Hasher(),
        sessions=DatabaseSessionIssuer(
            db,
            ttl=timedelta(minutes=settings.session_ttl_minutes),
        ),
    )


def _enforce_limit(
    limiter: RateLimiter,
    *,
    scope: str,
    subject: str,
    limit: int,
    window_seconds: int,
) -> None:
    try:
        decision = limiter.check(
            scope,
            subject,
            limit=limit,
            window_seconds=window_seconds,
        )
    except RateLimitBackendUnavailable as exc:
        raise auth_service_unavailable() from exc

    if not decision.allowed:
        raise rate_limited(decision.retry_after_seconds)


def _credential_source(request: Request, settings: Settings) -> str:
    if settings.auth_trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            first_hop = forwarded_for.split(",", 1)[0].strip()
            if first_hop:
                return first_hop

    if request.client is None:
        return "unknown"
    return request.client.host
