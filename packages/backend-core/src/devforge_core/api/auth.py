from dataclasses import dataclass
from hashlib import sha256
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from devforge_core.auth.abuse import (
    CredentialRateLimiter,
    RateLimitBackendUnavailable,
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
from devforge_core.client_address import resolve_client_address
from devforge_core.config import get_settings
from devforge_core.database import get_db
from devforge_core.users import SqlAlchemyUserProfileRepository

from .contracts import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
    UserProfileResponse,
)
from .errors import (
    invalid_credentials,
    not_authenticated,
    password_policy_violation,
    rate_limited,
    registration_failed,
    resource_not_found,
    temporarily_unavailable,
)

_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="DevForgeSession",
    description=(
        "Opaque DevForge session token for mobile/API transports. "
        "Browser JavaScript must use the server-mediated BFF/cookie transport instead."
    ),
)

_CREDENTIAL_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    actor: Actor
    raw_token: str


def get_credential_rate_limiter(
    redis: Annotated[Redis, Depends(get_redis)],
) -> CredentialRateLimiter:
    return RedisFixedWindowRateLimiter(redis)


def _auth_service(db: Session) -> AuthService:
    return AuthService(
        users=SqlAlchemyUserRepository(db),
        passwords=Argon2Hasher(),
        sessions=DatabaseSessionIssuer(db),
    )


def _stable_bucket(value: str) -> str:
    return sha256(value.strip().lower().encode("utf-8")).hexdigest()


def _client_bucket(request: Request, trusted_proxy_cidrs: list[str]) -> str:
    return _stable_bucket(resolve_client_address(request, trusted_proxy_cidrs))


def _identifier_bucket(identifier: str) -> str:
    return _stable_bucket(identifier)


async def _enforce_credential_limits(
    limiter: CredentialRateLimiter,
    *,
    operation: str,
    client_ip: str,
    identifier: str,
    ip_limit: int,
    identifier_limit: int,
    window_seconds: int,
) -> None:
    keys_and_limits = (
        (f"devforge:credential:{operation}:ip:{client_ip}", ip_limit),
        (
            f"devforge:credential:{operation}:identifier:{_identifier_bucket(identifier)}",
            identifier_limit,
        ),
    )
    try:
        for key, limit in keys_and_limits:
            decision = await limiter.check(
                key,
                limit=limit,
                window_seconds=window_seconds,
            )
            if not decision.allowed:
                raise rate_limited(decision.retry_after_seconds)
    except RateLimitBackendUnavailable as exc:
        raise temporarily_unavailable() from exc


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
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_CREDENTIAL_ERROR_RESPONSES,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    limiter: Annotated[CredentialRateLimiter, Depends(get_credential_rate_limiter)],
) -> UserProfileResponse:
    settings = get_settings()
    await _enforce_credential_limits(
        limiter,
        operation="register",
        client_ip=_client_bucket(request, settings.trusted_proxy_cidrs),
        identifier=payload.email,
        ip_limit=settings.register_ip_limit,
        identifier_limit=settings.register_identifier_limit,
        window_seconds=settings.credential_rate_limit_window_seconds,
    )

    try:
        actor = await _auth_service(db).register(
            RegisterCommand(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
            )
        )
    except EmailAlreadyExists as exc:
        raise registration_failed() from exc
    except PasswordPolicyViolation as exc:
        raise password_policy_violation(exc.reason) from exc

    profile = SqlAlchemyUserProfileRepository(db).get(actor.id)
    if profile is None:
        raise resource_not_found()
    response.headers["Cache-Control"] = "no-store"
    return UserProfileResponse.model_validate(profile, from_attributes=True)


@router.post(
    "/session",
    response_model=SessionResponse,
    responses=_CREDENTIAL_ERROR_RESPONSES,
)
async def create_session(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    limiter: Annotated[CredentialRateLimiter, Depends(get_credential_rate_limiter)],
) -> SessionResponse:
    settings = get_settings()
    await _enforce_credential_limits(
        limiter,
        operation="login",
        client_ip=_client_bucket(request, settings.trusted_proxy_cidrs),
        identifier=payload.identifier,
        ip_limit=settings.login_ip_limit,
        identifier_limit=settings.login_identifier_limit,
        window_seconds=settings.credential_rate_limit_window_seconds,
    )

    try:
        _actor, token = await _auth_service(db).login(
            LoginCommand(identifier=payload.identifier, password=payload.password)
        )
    except InvalidCredentials as exc:
        raise invalid_credentials() from exc

    response.headers["Cache-Control"] = "no-store"
    return SessionResponse(
        session_token=token,
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
