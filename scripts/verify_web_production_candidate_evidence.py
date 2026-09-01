#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "docs/evidence/web-production-candidate.json"
PILOT_PR_CREATED_AT_TEXT = "2026-08-22T15:26:03Z"
PILOT_PR_CREATED_AT = datetime.fromisoformat(PILOT_PR_CREATED_AT_TEXT.replace("Z", "+00:00"))

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
IMAGE_RE = re.compile(r"^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$")
SCHEMA_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")

REQUIRED_CONTROL_FILES = (
    "docs/13_PILOT_PROOF_METRICS.md",
    "infrastructure/staging/REAL_STAGING_RELEASE.md",
    "infrastructure/staging/OPERABILITY.md",
    "infrastructure/staging/observability/staging_monitor.py",
    "infrastructure/staging/scripts/record-release-meta.sh",
    "infrastructure/staging/scripts/release_guard.py",
    "infrastructure/staging/scripts/rollback-release.sh",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"production-candidate evidence invalid: {message}")


def require_exact_keys(value: object, expected: set[str], field: str) -> dict[str, object]:
    require(isinstance(value, dict), f"{field} must be an object")
    obj = value
    require(set(obj) == expected, f"{field} keys do not match schema")
    return obj


def parse_utc(value: object, field: str) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), f"{field} must be a UTC Z timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SystemExit(f"production-candidate evidence invalid: {field} is not ISO-8601") from exc
    require(parsed.tzinfo is not None, f"{field} must be timezone aware")
    return parsed.astimezone(timezone.utc)


def valid_public_https_origin(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        return False

    host = parsed.hostname.lower().rstrip(".")
    if (
        host == "localhost"
        or host.endswith(".localhost")
        or host.endswith(".test")
        or host.endswith(".invalid")
        or host.endswith(".example")
        or host.startswith("example.")
    ):
        return False

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def nonempty_reference(value: object, field: str) -> None:
    require(
        isinstance(value, str) and len(value.strip()) >= 3,
        f"{field} must contain an evidence reference",
    )


def verify_control_plane() -> None:
    for relative in REQUIRED_CONTROL_FILES:
        require((ROOT / relative).is_file(), f"required current control is missing: {relative}")

    metrics = (ROOT / "docs/13_PILOT_PROOF_METRICS.md").read_text(encoding="utf-8")
    require(
        f"PR #23 created: `{PILOT_PR_CREATED_AT_TEXT}`" in metrics,
        "pilot PR creation timestamp no longer matches the measured baseline",
    )

    monitor = (ROOT / "infrastructure/staging/observability/staging_monitor.py").read_text(
        encoding="utf-8"
    )
    require("--alert-drill" in monitor, "current staging monitor no longer exposes alert-drill proof")
    require(
        "STAGING_ALERT_WEBHOOK_URL" in monitor,
        "current staging monitor no longer exposes webhook alert delivery",
    )

    release_guard = (ROOT / "infrastructure/staging/scripts/release_guard.py").read_text(
        encoding="utf-8"
    )
    for marker in ("DIGEST_IMAGE_RE", "assert-schema-compatible", "workflow_run_id"):
        require(marker in release_guard, f"release guard is missing reviewed marker: {marker}")

    record = (ROOT / "infrastructure/staging/scripts/record-release-meta.sh").read_text(
        encoding="utf-8"
    )
    require("release_guard.py record" in record, "release metadata path no longer uses release_guard")

    rollback = (ROOT / "infrastructure/staging/scripts/rollback-release.sh").read_text(
        encoding="utf-8"
    )
    for marker in ("assert-schema-compatible", "deploy-release.sh"):
        require(marker in rollback, f"rollback control is missing reviewed marker: {marker}")


def load_evidence(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"production-candidate evidence invalid: unable to load evidence: {type(exc).__name__}"
        ) from exc
    require(isinstance(data, dict), "evidence root must be an object")
    return data


def verify_evidence(data: dict[str, object]) -> None:
    require_exact_keys(data, {"schema_version", "pilot_id", "status", "production_candidate"}, "root")
    require(data["schema_version"] == 2, "schema_version must be 2")
    require(data["pilot_id"] == "generated-web-auth", "unexpected pilot_id")
    require(data["status"] in {"open_not_reached", "production_candidate"}, "unsupported status")

    pc = require_exact_keys(
        data["production_candidate"],
        {
            "completed_at",
            "seconds_from_pilot_pr_open",
            "staging_origin",
            "release",
            "real_staging",
            "monitoring",
            "rollback_drill",
        },
        "production_candidate",
    )
    release = require_exact_keys(
        pc["release"],
        {
            "source_sha",
            "backend_image",
            "web_image",
            "database_schema_head",
            "workflow_run_id",
            "deployed_at",
            "metadata_reference",
            "backup_checksum_reference",
            "release_notes_reference",
            "operator_reference",
        },
        "production_candidate.release",
    )
    real = require_exact_keys(
        pc["real_staging"],
        {"public_tls", "service_isolation", "browser_e2e", "backup_restore"},
        "production_candidate.real_staging",
    )
    monitoring = require_exact_keys(
        pc["monitoring"],
        {
            "external_log_collection",
            "public_uptime_monitor",
            "backend_health_monitor",
            "alert_delivery_test",
            "evidence_reference",
        },
        "production_candidate.monitoring",
    )
    rollback = require_exact_keys(
        pc["rollback_drill"],
        {
            "status",
            "previous_release_source_sha",
            "previous_backend_image",
            "previous_web_image",
            "pre_rollback_backup_reference",
            "completed_at",
            "evidence_reference",
        },
        "production_candidate.rollback_drill",
    )

    if data["status"] == "open_not_reached":
        for key in ("completed_at", "seconds_from_pilot_pr_open", "staging_origin"):
            require(pc[key] is None, f"open baseline cannot claim {key}")
        require(all(value is None for value in release.values()), "open release record must stay empty")
        require(set(real.values()) == {"open"}, "all real-staging gates must remain open")
        for key in (
            "external_log_collection",
            "public_uptime_monitor",
            "backend_health_monitor",
            "alert_delivery_test",
        ):
            require(monitoring[key] == "open", f"monitoring.{key} must remain open")
        require(monitoring["evidence_reference"] is None, "open baseline cannot claim monitoring evidence")
        require(rollback["status"] == "open", "rollback drill must remain open")
        require(
            all(
                rollback[key] is None
                for key in (
                    "previous_release_source_sha",
                    "previous_backend_image",
                    "previous_web_image",
                    "pre_rollback_backup_reference",
                    "completed_at",
                    "evidence_reference",
                )
            ),
            "open rollback baseline cannot contain completed evidence",
        )
        print("Web Production Candidate evidence: OPEN / NOT REACHED (baseline valid).")
        return

    completed_at = parse_utc(pc["completed_at"], "production_candidate.completed_at")
    require(completed_at >= PILOT_PR_CREATED_AT, "completed_at predates pilot PR")
    require(
        valid_public_https_origin(pc["staging_origin"]),
        "staging_origin must be a real public HTTPS origin",
    )
    expected_seconds = int((completed_at - PILOT_PR_CREATED_AT).total_seconds())
    require(
        pc["seconds_from_pilot_pr_open"] == expected_seconds,
        "production-candidate duration does not recompute from pilot PR open",
    )

    source_sha = release["source_sha"]
    require(
        isinstance(source_sha, str) and SHA_RE.fullmatch(source_sha),
        "release.source_sha must be a lowercase 40-character SHA",
    )
    for key in ("backend_image", "web_image"):
        value = release[key]
        require(
            isinstance(value, str) and IMAGE_RE.fullmatch(value),
            f"release.{key} must be an immutable GHCR @sha256 image",
        )
    require(
        isinstance(release["database_schema_head"], str)
        and SCHEMA_RE.fullmatch(release["database_schema_head"]),
        "release.database_schema_head is invalid",
    )
    require(
        isinstance(release["workflow_run_id"], int)
        and not isinstance(release["workflow_run_id"], bool)
        and release["workflow_run_id"] > 0,
        "release.workflow_run_id must be a positive integer",
    )
    deployed_at = parse_utc(release["deployed_at"], "production_candidate.release.deployed_at")
    require(deployed_at <= completed_at, "release.deployed_at cannot be after completed_at")
    for key in (
        "metadata_reference",
        "backup_checksum_reference",
        "release_notes_reference",
        "operator_reference",
    ):
        nonempty_reference(release[key], f"production_candidate.release.{key}")

    for key in ("public_tls", "service_isolation", "browser_e2e", "backup_restore"):
        require(real[key] == "success", f"real_staging.{key} must be success")

    for key in (
        "external_log_collection",
        "public_uptime_monitor",
        "backend_health_monitor",
        "alert_delivery_test",
    ):
        require(monitoring[key] == "success", f"monitoring.{key} must be success")
    nonempty_reference(monitoring["evidence_reference"], "monitoring.evidence_reference")

    require(rollback["status"] == "success", "rollback drill must be successful")
    previous_sha = rollback["previous_release_source_sha"]
    require(
        isinstance(previous_sha, str) and SHA_RE.fullmatch(previous_sha),
        "rollback previous release SHA is invalid",
    )
    require(previous_sha != source_sha, "rollback drill must use a materially previous source SHA")
    for key in ("previous_backend_image", "previous_web_image"):
        value = rollback[key]
        require(
            isinstance(value, str) and IMAGE_RE.fullmatch(value),
            f"rollback_drill.{key} must be an immutable GHCR @sha256 image",
        )
    nonempty_reference(
        rollback["pre_rollback_backup_reference"],
        "rollback_drill.pre_rollback_backup_reference",
    )
    rollback_completed_at = parse_utc(
        rollback["completed_at"], "production_candidate.rollback_drill.completed_at"
    )
    require(rollback_completed_at <= completed_at, "rollback drill cannot complete after candidate")
    nonempty_reference(rollback["evidence_reference"], "rollback_drill.evidence_reference")

    print(
        f"Web Production Candidate evidence: VERIFIED at {pc['completed_at']} "
        f"({expected_seconds}s from pilot PR open)."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    verify_control_plane()
    verify_evidence(load_evidence(args.evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
