#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/web-production-candidate.json"
PILOT_PR_CREATED_AT = datetime.fromisoformat("2026-08-22T15:26:03+00:00")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
IMAGE_RE = re.compile(r"^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"production-candidate evidence invalid: {message}")


def parse_utc(value: str, field: str) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), f"{field} must be UTC Z timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SystemExit(f"production-candidate evidence invalid: {field} is not ISO-8601") from exc
    require(parsed.tzinfo is not None, f"{field} must be timezone aware")
    return parsed.astimezone(timezone.utc)


def valid_https_origin(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname or parsed.path not in ("", "/"):
        return False
    host = parsed.hostname.lower()
    blocked = ("example.", ".example", ".test", ".invalid", "localhost")
    return not any(part in host for part in blocked) and host not in {"127.0.0.1", "::1"}


def nonempty_reference(value: object, field: str) -> None:
    require(isinstance(value, str) and len(value.strip()) >= 3, f"{field} must contain an evidence reference")


def main() -> None:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(data.get("pilot_id") == "generated-web-auth", "unexpected pilot_id")
    require(data.get("status") in {"open_not_reached", "production_candidate"}, "unsupported status")

    pc = data.get("production_candidate")
    require(isinstance(pc, dict), "production_candidate must be an object")

    real = pc.get("real_staging")
    monitoring = pc.get("monitoring")
    rollback = pc.get("rollback_drill")
    release = pc.get("release_record")
    require(all(isinstance(item, dict) for item in (real, monitoring, rollback, release)), "evidence sections must be objects")

    if data["status"] == "open_not_reached":
        require(pc.get("source_sha") is None, "open baseline cannot claim source_sha")
        require(pc.get("completed_at") is None, "open baseline cannot claim completed_at")
        require(pc.get("seconds_from_pilot_pr_open") is None, "open baseline cannot claim duration")
        require(pc.get("staging_origin") is None, "open baseline cannot claim staging origin")
        require(pc.get("backend_image") is None and pc.get("web_image") is None, "open baseline cannot claim image digests")
        require(pc.get("real_staging_workflow_run_id") is None, "open baseline cannot claim real staging run")
        require(set(real.values()) == {"open"}, "all real-staging gates must remain open until evidenced")
        for key in ("external_log_collection", "public_uptime_monitor", "backend_health_monitor", "alert_delivery_test"):
            require(monitoring.get(key) == "open", f"monitoring.{key} must remain open")
        require(monitoring.get("evidence_reference") is None, "open baseline cannot claim monitoring evidence")
        require(rollback.get("status") == "open", "rollback drill must remain open")
        require(all(rollback.get(key) is None for key in (
            "previous_release_source_sha", "previous_backend_image", "previous_web_image",
            "backup_reference", "completed_at", "evidence_reference"
        )), "open rollback baseline cannot contain completed evidence")
        require(all(value is None for value in release.values()), "open release record cannot contain completed evidence")
        print("Web Production Candidate evidence: OPEN / NOT REACHED (baseline valid).")
        return

    source_sha = pc.get("source_sha")
    require(isinstance(source_sha, str) and SHA_RE.fullmatch(source_sha), "source_sha must be a lowercase 40-char SHA")
    require(valid_https_origin(pc.get("staging_origin", "")), "staging_origin must be a real HTTPS origin")
    require(isinstance(pc.get("backend_image"), str) and IMAGE_RE.fullmatch(pc["backend_image"]), "backend_image must be immutable GHCR digest")
    require(isinstance(pc.get("web_image"), str) and IMAGE_RE.fullmatch(pc["web_image"]), "web_image must be immutable GHCR digest")
    require(isinstance(pc.get("real_staging_workflow_run_id"), int) and pc["real_staging_workflow_run_id"] > 0, "real staging workflow run id required")

    completed_at = parse_utc(pc.get("completed_at"), "completed_at")
    require(completed_at >= PILOT_PR_CREATED_AT, "completed_at predates pilot PR")
    expected_seconds = int((completed_at - PILOT_PR_CREATED_AT).total_seconds())
    require(pc.get("seconds_from_pilot_pr_open") == expected_seconds, "production-candidate duration does not recompute")

    for key in ("public_tls", "service_isolation", "browser_e2e", "backup_restore"):
        require(real.get(key) == "success", f"real_staging.{key} must be success")

    for key in ("external_log_collection", "public_uptime_monitor", "backend_health_monitor", "alert_delivery_test"):
        require(monitoring.get(key) == "success", f"monitoring.{key} must be success")
    nonempty_reference(monitoring.get("evidence_reference"), "monitoring.evidence_reference")

    require(rollback.get("status") == "success", "rollback drill must be successful")
    require(isinstance(rollback.get("previous_release_source_sha"), str) and SHA_RE.fullmatch(rollback["previous_release_source_sha"]), "previous release SHA required")
    require(rollback["previous_release_source_sha"] != source_sha, "rollback drill must use a materially previous source SHA")
    require(isinstance(rollback.get("previous_backend_image"), str) and IMAGE_RE.fullmatch(rollback["previous_backend_image"]), "previous backend digest required")
    require(isinstance(rollback.get("previous_web_image"), str) and IMAGE_RE.fullmatch(rollback["previous_web_image"]), "previous web digest required")
    nonempty_reference(rollback.get("backup_reference"), "rollback_drill.backup_reference")
    parse_utc(rollback.get("completed_at"), "rollback_drill.completed_at")
    nonempty_reference(rollback.get("evidence_reference"), "rollback_drill.evidence_reference")

    for key in ("migration_head", "backup_checksum_reference", "release_notes_reference", "operator_reference"):
        nonempty_reference(release.get(key), f"release_record.{key}")

    print(f"Web Production Candidate evidence: VERIFIED at {pc['completed_at']} ({expected_seconds}s from pilot PR open).")


if __name__ == "__main__":
    main()
