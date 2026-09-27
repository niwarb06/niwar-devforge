from datetime import UTC, datetime

import pytest

from devforge_core.audit import AuditEvent, AuditSink


class MemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


def record_with_sink(sink: AuditSink, event: AuditEvent) -> None:
    sink.record(event)


def test_audit_event_preserves_context_and_copies_metadata() -> None:
    source_metadata = {"reason": "manual_review"}
    event = AuditEvent(
        action="roles.assign",
        outcome="success",
        occurred_at=datetime(2026, 9, 27, 13, 0, tzinfo=UTC),
        actor_id="actor-1",
        tenant_id="tenant-1",
        target_type="user",
        target_id="user-2",
        request_id="request-1",
        metadata=source_metadata,
    )

    source_metadata["reason"] = "changed"

    assert event.action == "roles.assign"
    assert event.outcome == "success"
    assert event.request_id == "request-1"
    assert event.metadata == {"reason": "manual_review"}


def test_audit_event_rejects_blank_action() -> None:
    with pytest.raises(ValueError, match="action"):
        AuditEvent(
            action="   ",
            outcome="success",
            occurred_at=datetime.now(UTC),
        )


def test_audit_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        AuditEvent(
            action="session.revoke",
            outcome="success",
            occurred_at=datetime(2026, 9, 27, 13, 0),
        )


def test_audit_event_rejects_non_string_metadata() -> None:
    with pytest.raises(ValueError, match="metadata"):
        AuditEvent(
            action="profile.update",
            outcome="failure",
            occurred_at=datetime.now(UTC),
            metadata={"attempt": 1},  # type: ignore[dict-item]
        )


def test_audit_sink_protocol_accepts_provider_neutral_sink() -> None:
    sink = MemoryAuditSink()
    event = AuditEvent(
        action="session.revoke",
        outcome="success",
        occurred_at=datetime.now(UTC),
    )

    record_with_sink(sink, event)

    assert sink.events == [event]
