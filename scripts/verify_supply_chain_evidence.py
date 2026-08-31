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

# Trivy 0.74.0 reports these SPDX licenses with severity UNKNOWN because its
# license policy has no risk classification for them. They were reviewed as
# permissive, but the exception is intentionally bound to the exact report,
# package, installed version, and license expression. Any drift fails closed.
REVIEWED_TRIVY_UNKNOWN_LICENSES = {
    ("backend-license.json", "cffi", "2.1.1", "MIT-0"),
    ("backend-license.json", "greenlet", "3.5.5", "MIT AND PSF-2.0"),
    ("backend-license.json", "typing-extensions", "4.16.0", "PSF-2.0"),
}


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


def normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pip_freeze(path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "==" not in line:
            die(f"{path.name} contains a non-exact requirement: {line}")
        name, version = line.split("==", 1)
        name = normalize_package_name(name.strip())
        version = version.strip()
        if not name or not version:
            die(f"{path.name} contains a malformed requirement: {line}")
        if name in versions:
            die(f"{path.name} contains duplicate package {name!r}")
        versions[name] = version
    if not versions:
        die(f"{path.name} contains no installed packages")
    return versions


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


def verify_trivy_license_report(
    path: Path,
    package_versions: dict[str, str] | None = None,
) -> tuple[int, int, int]:
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

    blocking: list[tuple[dict[str, Any], str]] = []
    review: list[dict[str, Any]] = []
    reviewed_unknown: list[dict[str, Any]] = []
    for item in licenses:
        package_name = str(item.get("PkgName", "")).strip()
        license_name = str(item.get("Name", "")).strip()
        severity = str(item.get("Severity", "UNKNOWN")).upper()
        if not package_name or not license_name:
            blocking.append((item, "missing package/license identity"))
            continue

        if severity == "LOW":
            continue
        if severity in {"HIGH", "MEDIUM"}:
            review.append(item)
            continue
        if severity == "CRITICAL":
            blocking.append((item, "critical license classification"))
            continue
        if severity == "UNKNOWN":
            normalized_package = normalize_package_name(package_name)
            version = ""
            if package_versions is not None:
                version = package_versions.get(normalized_package, "")
            key = (path.name, normalized_package, version, license_name)
            if key in REVIEWED_TRIVY_UNKNOWN_LICENSES:
                reviewed_unknown.append(item)
            else:
                blocking.append((item, "unreviewed UNKNOWN classification"))
            continue

        blocking.append((item, f"unexpected Trivy severity {severity!r}"))

    if blocking:
        details = ", ".join(
            sorted(
                {
                    (
                        f"{item.get('PkgName', '?')}@"
                        f"{(package_versions or {}).get(normalize_package_name(str(item.get('PkgName', '?'))), '?')}:"
                        f"{item.get('Name', '?')}:{item.get('Severity', '?')} ({reason})"
                    )
                    for item, reason in blocking
                }
            )
        )
        die(f"{path.name} has forbidden/unreviewed license findings: {details}")

    return len(licenses), len(review), len(reviewed_unknown)


def verify_dart_graph(path: Path) -> tuple[str, set[str], dict[str, Any]]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        die(f"{path.name} is not a JSON object")
    root = payload.get("root")
    packages = payload.get("packages")
    if not isinstance(root, str) or not root:
        die(f"{path.name} has no root package")
    if not isinstance(packages, list) or not packages:
        die(f"{path.name} has no packages")

    names: set[str] = set()
    root_package: dict[str, Any] | None = None
    for package in packages:
        if not isinstance(package, dict):
            die(f"{path.name} contains a non-object package")
        name = package.get("name")
        if not isinstance(name, str) or not name:
            die(f"{path.name} contains a package without a name")
        if name in names:
            die(f"{path.name} contains duplicate package {name!r}")
        names.add(name)
        if name == root:
            root_package = package

    if root_package is None:
        die(f"{path.name} does not contain its root package")
    return root, names, root_package


def verify_flutter_graphs(root: Path) -> tuple[int, int]:
    full_root, full_names, full_root_package = verify_dart_graph(root / "flutter-full-deps.json")
    runtime_root, runtime_names, runtime_root_package = verify_dart_graph(
        root / "flutter-runtime-deps.json"
    )

    if full_root != runtime_root:
        die("Flutter full/runtime dependency graphs have different roots")
    if not runtime_names.issubset(full_names):
        unexpected = sorted(runtime_names - full_names)
        die(f"Flutter runtime graph contains packages absent from full graph: {unexpected}")

    full_dev = full_root_package.get("devDependencies", [])
    full_direct = full_root_package.get("directDependencies", [])
    runtime_direct = runtime_root_package.get("directDependencies", [])
    runtime_dev = runtime_root_package.get("devDependencies", [])
    for field_name, value in (
        ("full devDependencies", full_dev),
        ("full directDependencies", full_direct),
        ("runtime directDependencies", runtime_direct),
        ("runtime devDependencies", runtime_dev),
    ):
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            die(f"Flutter {field_name} is not a package-name list")

    if runtime_dev:
        die("Flutter runtime graph still declares devDependencies")
    if set(runtime_direct) != set(full_direct):
        die("Flutter runtime graph changed the root runtime/direct dependency set")

    dev_only = set(full_dev) - set(full_direct)
    leaked_dev = sorted(dev_only & runtime_names)
    if leaked_dev:
        die(f"Flutter runtime graph retains dev-only packages: {', '.join(leaked_dev)}")

    return len(full_names), len(runtime_names)


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
    for marker in (
        "Trivy 0.74.0",
        "license_checker 1.6.2",
        "Node",
        "npm",
        "Flutter",
        "Dart",
        "Python",
    ):
        if marker not in tool_versions:
            die(f"tool-versions.txt is missing {marker!r}")

    cdx_counts = {
        "web-full": verify_cyclonedx(root / "web-full.cdx.json"),
        "web-runtime": verify_cyclonedx(root / "web-runtime.cdx.json"),
        "backend-runtime": verify_cyclonedx(root / "backend-runtime.cdx.json"),
        "flutter-lock": verify_cyclonedx(root / "flutter-lock.cdx.json"),
    }

    backend_versions = parse_pip_freeze(root / "backend-freeze.txt")
    web_licenses, web_review, web_reviewed_unknown = verify_trivy_license_report(
        root / "web-license.json"
    )
    backend_licenses, backend_review, backend_reviewed_unknown = verify_trivy_license_report(
        root / "backend-license.json", backend_versions
    )
    flutter_full_count, flutter_runtime_count = verify_flutter_graphs(root)

    read_text(root / "web-package-lock.json")
    read_text(root / "flutter-license-audit.txt")
    read_text(root / "flutter-pubspec.lock")
    verify_hashes(root)

    print("Supply-chain evidence PASS")
    print("CycloneDX component counts:", json.dumps(cdx_counts, sort_keys=True))
    print(
        f"Web licenses: {web_licenses} total; {web_review} require release review (HIGH/MEDIUM); "
        f"{web_reviewed_unknown} exact UNKNOWN mappings reviewed"
    )
    print(
        f"Backend licenses: {backend_licenses} total; "
        f"{backend_review} require release review (HIGH/MEDIUM); "
        f"{backend_reviewed_unknown} exact UNKNOWN mappings reviewed"
    )
    print(
        f"Flutter dependency graph: {flutter_full_count} full / "
        f"{flutter_runtime_count} runtime packages"
    )
    print("Flutter license_checker allowlist: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
