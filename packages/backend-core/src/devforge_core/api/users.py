from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from devforge_core.auth.contracts import Actor
from devforge_core.auth.permissions import default_authorization_policy
from devforge_core.database import get_db
from devforge_core.users import SqlAlchemyUserProfileRepository, UpdateProfileCommand

from .auth import get_current_actor
from .contracts import ErrorResponse, UpdateProfileRequest, UserProfileResponse
from .errors import permission_denied, resource_not_found

router = APIRouter(prefix="/users", tags=["users"])

_ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}


def _to_response(profile: object) -> UserProfileResponse:
    return UserProfileResponse.model_validate(profile, from_attributes=True)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses=_ERROR_RESPONSES,
)
def get_my_profile(
    actor: Annotated[Actor, Depends(get_current_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfileResponse:
    policy = default_authorization_policy()
    if not policy.allows(actor, "profile.read:self"):
        raise permission_denied()

    profile = SqlAlchemyUserProfileRepository(db).get(actor.id)
    if profile is None:
        raise resource_not_found()
    return _to_response(profile)


@router.patch(
    "/me/profile",
    response_model=UserProfileResponse,
    responses=_ERROR_RESPONSES,
)
def update_my_profile(
    request: UpdateProfileRequest,
    actor: Annotated[Actor, Depends(get_current_actor)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfileResponse:
    policy = default_authorization_policy()
    if not policy.allows(actor, "profile.write:self"):
        raise permission_denied()

    profile = SqlAlchemyUserProfileRepository(db).update(
        actor.id,
        UpdateProfileCommand(display_name=request.display_name),
    )
    if profile is None:
        raise resource_not_found()
    return _to_response(profile)
