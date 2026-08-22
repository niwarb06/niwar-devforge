#!/usr/bin/env python3
"""Validate and record immutable staging release metadata for safe rollback decisions."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_IMAGE_RE = re.compile(r"^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$")
SCHEMA_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_payload(payload: dict[str, object]) -> dict[str, object]:
    required = {
        "schema_version",
        "source_sha",
        "backend_image",
        "web_image",
        "database_schema_head",
        "workflow_run_id",
        "deployed_at",
    }
    if set(payload) != required:
        raise ValueError("release metadata keys do not match the expected schema")
    if payload["schema_version"] != 1:
        raise ValueError("unsupported release metadata schema version")
    if not isinstance(payload["source_sha"], str) or not SHA_RE.fullmatch(payload["source_sha"]):
        raise ValueError("source_sha must be a lowercase 40-character commit SHA")
    for key in ("backend_image", "web_image"):
        value = payload[key]
        if not isinstance(value, str) or not DIGEST_IMAGE_RE.fullmatch(value):
            raise ValueError(f"{key} must be an immutable GHCR @sha256 image reference")
    schema_head = payload["database_schema_head"]
    if not isinstance(schema_head, str) or not SCHEMA_RE.fullmatch(schema_head):
        raise ValueError("database_schema_head is invalid")
    run_id = payload["workflow_run_id"]
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise ValueError("workflow_run_id must be a positive integer")
    deployed_at = payload["deployed_at"]
    if not isinstance(deployed_at, str) or not deployed_at.endswith("Z"):
        raise ValueError("deployed_at must be an explicit UTC timestamp")
    try:
        datetime.fromisoformat(deployed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("deployed_at is not a valid timestamp") from exc
    return payload


def load(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to load release metadata: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise ValueError("release metadata must be a JSON object")
    return validate_payload(payload)


def write(path: Path, payload: dict[str, object]) -> None:
    validate_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--path", required=True, type=Path)
    record.add_argument("--source-sha", required=True)
    record.add_argument("--backend-image", required=True)
    record.add_argument("--web-image", required=True)
    record.add_argument("--database-schema-head", required=True)
    record.add_argument("--workflow-run-id", required=True, type=int)

    validate = sub.add_parser("validate")
    validate.add_argument("--path", required=True, type=Path)

    compatible = sub.add_parser("assert-schema-compatible")
    compatible.add_argument("--path", required=True, type=Path)
    compatible.add_argument("--current-schema-head", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "record":
        payload = {
            "schema_version": 1,
            "source_sha": args.source_sha,
            "backend_image": args.backend_image,
            "web_image": args.web_image,
            "database_schema_head": args.database_schema_head,
            "workflow_run_id": args.workflow_run_id,
            "deployed_at": utc_now(),
        }
        write(args.path, payload)
        print(f"recorded release metadata at {args.path}")
        return 0

    payload = load(args.path)
    if args.command == "validate":
        print(f"release metadata valid for {payload['source_sha']}")
        return 0

    current = args.current_schema_head
    if not SCHEMA_RE.fullmatch(current):
        raise SystemExit("current schema head is invalid")
    expected = str(payload["database_schema_head"])
    if current != expected:
        raise SystemExit(
            "rollback blocked: current database schema head does not exactly match the target release"
        )
    print(f"rollback schema compatibility confirmed at {current}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
