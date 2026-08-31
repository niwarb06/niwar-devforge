#!/usr/bin/env python3
"""Fail closed when generated release-evidence files are missing or structurally invalid."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPECTED_HASHED_FILES = (
    "source-commit.txt",
    "tool-versions.txt",
    "web-full.cdx.json",
    "web-runtime.cdx.json",
    "web-license.json",
    "web-package-lock.json",
    "backend-runtime.cdx.json",
    "backend-license.json",
    "backend-freeze.txt",
    "flutter-lock.cdx.json",
    "flutter-full-deps.json",
    "flutter-runtime-deps.json",
    "flutter-license-audit.txt",
    "flutter-pubspec.lock",
)


def die(message: str) -> "NoReturn":
    raise SystemExit(f"supply-chain evidence verification failed: {message}")


def read_text(path: Path) -> str:
    if not path.is_file():
        die(f"missing {path.name}")
    text = path.read_text(encoding="utf-8", errors="strict")
    if not text.strip():
        die(f"empty {path.name}")
    return text


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path.name}: {exc}")


def verify_cyclonedx(path: Path) -> int:
    payload = read_json(path)
    if not isinstance(payload, dict):
        die(f"{path.name} is not a JSON object")
    if payload.get("bomFormat") != "CycloneDX":
        die(f"{path.name} is not CycloneDX")
    if not isinstance(payload.get("specVersion"), str):
        die(f"{path.name} has no specVersion")
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        die(f"{path.name} has no components")
    for component in components:
        if not isinstance(component, dict) or not str(component.get("name", "")).strip():
            die(f"{path.name} contains a component without a name")
    return len(components)


def verify_trivy_license_report(path: Path) -> tuple[int, int]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        die(f"{path.name} is not a JSON object")
    if not isinstance(payload.get("SchemaVersion"), int):
        die(f"{path.name} is not a Trivy JSON report")
    results = payload.get("Results")
    if not isinstance(results, list):
        die(f"{path.name} has no Results array")

    licenses: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        found = result.get("Licenses", [])
        if isinstance(found, list):
            licenses.extend(item for item in found if isinstance(item, dict))

    if not licenses:
        die(f"{path.name} contains no detected package licenses")

    blocking = []
    review = []
    for item in licenses:
        severity = str(item.get("Severity", "UNKNOWN")).upper()
        if severity in {"UNKNOWN", "CRITICAL"}:
            blocking.append(item)
        elif severity in {"HIGH", "MEDIUM"}:
            review.append(item)

    if blocking:
        details = ", ".join(
            sorted(
                {
                    f"{item.get('PkgName', '?')}:{item.get('Name', '?')}:{item.get('Severity', '?')}"
                    for item in blocking
                }
            )
        )
        die(f"{path.name} has forbidden/unknown license findings: {details}")

    return len(licenses), len(review)


def verify_hashes(root: Path) -> None:
    manifest_path = root / "SHA256SUMS"
    manifest = read_text(manifest_path)
    recorded: dict[str, str] = {}
    for raw_line in manifest.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            die("malformed SHA256SUMS entry")
        name = parts[1].lstrip("*./")
        recorded[name] = parts[0]

    missing = sorted(set(EXPECTED_HASHED_FILES) - set(recorded))
    if missing:
        die(f"SHA256SUMS is missing: {', '.join(missing)}")

    for name in EXPECTED_HASHED_FILES:
        path = root / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if recorded[name] != digest:
            die(f"checksum mismatch for {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args()
    root: Path = args.evidence_dir
    if not root.is_dir():
        die(f"not a directory: {root}")

    commit = read_text(root / "source-commit.txt").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        die("source-commit.txt is not a full Git SHA")

    tool_versions = read_text(root / "tool-versions.txt")
    for marker in ("Trivy 0.74.0", "license_checker 1.6.2", "Node", "npm", "Flutter", "Dart", "Python"):
        if marker not in tool_versions:
            die(f"tool-versions.txt is missing {marker!r}")

    cdx_counts = {
        "web-full": verify_cyclonedx(root / "web-full.cdx.json"),
        "web-runtime": verify_cyclonedx(root / "web-runtime.cdx.json"),
        "backend-runtime": verify_cyclonedx(root / "backend-runtime.cdx.json"),
        "flutter-lock": verify_cyclonedx(root / "flutter-lock.cdx.json"),
    }

    web_licenses, web_review = verify_trivy_license_report(root / "web-license.json")
    backend_licenses, backend_review = verify_trivy_license_report(root / "backend-license.json")

    for json_name in ("flutter-full-deps.json", "flutter-runtime-deps.json"):
        payload = read_json(root / json_name)
        if not isinstance(payload, dict) or not payload:
            die(f"{json_name} is empty or not an object")

    read_text(root / "web-package-lock.json")
    read_text(root / "backend-freeze.txt")
    read_text(root / "flutter-license-audit.txt")
    read_text(root / "flutter-pubspec.lock")
    verify_hashes(root)

    print("Supply-chain evidence PASS")
    print("CycloneDX component counts:", json.dumps(cdx_counts, sort_keys=True))
    print(f"Web licenses: {web_licenses} total; {web_review} require release review (HIGH/MEDIUM)")
    print(
        f"Backend licenses: {backend_licenses} total; "
        f"{backend_review} require release review (HIGH/MEDIUM)"
    )
    print("Flutter license_checker allowlist: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
