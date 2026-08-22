from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from devforge_core.auth.contracts import Actor
from devforge_core.auth.sessions import DatabaseSessionIssuer
from devforge_core.database import get_db

from .contracts import ErrorResponse
from .errors import not_authenticated

_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="DevForgeSession",
    description=(
        "Opaque DevForge session token for mobile/API transports. "
        "Browser JavaScript must use the server-mediated BFF/cookie transport instead."
    ),
)


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    actor: Actor
    raw_token: str


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
