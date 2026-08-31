#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str) -> None:
    raise SystemExit(f"open-source-readiness: {message}")


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def verify_required_files() -> None:
    for path in (
        "LICENSE",
        "NOTICE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "THIRD_PARTY_NOTICES.md",
        "docs/19_OPEN_SOURCE_READINESS.md",
    ):
        read(path)

    license_text = read("LICENSE")
    if "Apache License" not in license_text or "Version 2.0, January 2004" not in license_text:
        fail("root LICENSE is not the expected Apache-2.0 text")

    for package in (
        "packages/backend-core",
        "packages/flutter-auth-core",
        "packages/web-bff-core",
        "packages/web-session-core",
    ):
        if (ROOT / package / "LICENSE").read_text(encoding="utf-8") != license_text:
            fail(f"{package}/LICENSE must match the root Apache-2.0 license")
        if not (ROOT / package / "NOTICE").is_file():
            fail(f"missing {package}/NOTICE")


def verify_package_metadata() -> None:
    for path in (
        "packages/web-bff-core/package.json",
        "packages/web-session-core/package.json",
    ):
        metadata = json.loads(read(path))
        if metadata.get("license") != "Apache-2.0":
            fail(f"{path} must declare license Apache-2.0")
        files = metadata.get("files", [])
        if "NOTICE" not in files:
            fail(f"{path} must include NOTICE in packed files")

    if 'license = "Apache-2.0"' not in read("packages/backend-core/pyproject.toml"):
        fail("backend-core pyproject.toml must declare Apache-2.0")


def verify_action_pins() -> None:
    violations: list[str] = []
    for workflow in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
        for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            match = re.search(r"\buses:\s*([^\s#]+)", line)
            if not match:
                continue
            target = match.group(1)
            if target.startswith("./") or target.startswith("docker://"):
                continue
            if "@" not in target:
                violations.append(f"{workflow.relative_to(ROOT)}:{number}: {target}")
                continue
            ref = target.rsplit("@", 1)[1]
            if not SHA40.fullmatch(ref):
                violations.append(f"{workflow.relative_to(ROOT)}:{number}: {target}")
    if violations:
        fail("remote GitHub Actions must use full commit SHAs:\n" + "\n".join(violations))


def verify_open_server_baseline() -> None:
    paths = [
        ROOT / "infrastructure/dev/docker-compose.yml",
        ROOT / "infrastructure/staging/compose.yml",
        *sorted((ROOT / ".github/workflows").glob("*.y*ml")),
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*image:\s*redis(?::|@)", text):
            fail(f"Redis server image remains in open-source baseline: {path.relative_to(ROOT)}")

    for path in (
        "infrastructure/dev/docker-compose.yml",
        "infrastructure/staging/compose.yml",
    ):
        if "valkey/valkey:7.2.14-alpine" not in read(path):
            fail(f"{path} must pin Valkey 7.2.14-alpine")


def main() -> None:
    verify_required_files()
    verify_package_metadata()
    verify_action_pins()
    verify_open_server_baseline()
    print("Open-source readiness repository invariants: PASS")


if __name__ == "__main__":
    main()
