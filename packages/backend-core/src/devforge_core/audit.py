from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Literal, Mapping, Protocol

AuditOutcome = Literal["success", "failure"]


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Provider-neutral audit event contract for security-relevant actions."""

    action: str
    outcome: AuditOutcome
    occurred_at: datetime
    actor_id: str | None = None
    tenant_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    request_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise ValueError("audit action must be non-empty")
        if self.outcome not in {"success", "failure"}:
            raise ValueError("audit outcome must be success or failure")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("audit occurred_at must be timezone-aware")

        metadata = dict(self.metadata)
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()):
            raise ValueError("audit metadata keys and values must be strings")
        object.__setattr__(self, "metadata", MappingProxyType(metadata))


class AuditSink(Protocol):
    """Persistence/export boundary for audit events."""

    def record(self, event: AuditEvent) -> None:
        """Record one audit event without exposing provider details to callers."""
