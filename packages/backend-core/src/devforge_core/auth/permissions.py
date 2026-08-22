from dataclasses import dataclass

from .contracts import Actor


@dataclass(frozen=True, slots=True)
class RolePermissionPolicy:
    role_permissions: dict[str, frozenset[str]]

    def allows(self, actor: Actor, permission: str) -> bool:
        return any(
            "*" in self.role_permissions.get(role, frozenset())
            or permission in self.role_permissions.get(role, frozenset())
            for role in actor.roles
        )


DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "user": frozenset({"profile.read:self", "profile.write:self"}),
    "admin": frozenset({"*"}),
}


def default_authorization_policy() -> RolePermissionPolicy:
    return RolePermissionPolicy(DEFAULT_ROLE_PERMISSIONS)
