from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import Actor


@dataclass(frozen=True, slots=True)
class RolePermissionPolicy:
    role_permissions: Mapping[str, frozenset[str]]

    def allows(self, actor: Actor, permission: str) -> bool:
        return any(
            "*" in self.role_permissions.get(role, frozenset())
            or permission in self.role_permissions.get(role, frozenset())
            for role in actor.roles
        )


DEFAULT_ROLE_PERMISSIONS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "user": frozenset({"profile.read:self", "profile.write:self"}),
        "member": frozenset({"tenant.read", "profile.read:self", "profile.write:self"}),
        "owner": frozenset({"tenant.read", "tenant.write", "tenant.members.manage"}),
        "admin": frozenset({"*"}),
    }
)


def default_authorization_policy() -> RolePermissionPolicy:
    return RolePermissionPolicy(DEFAULT_ROLE_PERMISSIONS)
