#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".sbom-evidence"
SBOM_PATH = EVIDENCE / "devforge.cdx.json"
LICENSE_PATH = EVIDENCE / "licenses.json"
SUMMARY_PATH = EVIDENCE / "summary.json"
EXPECTED_TRIVY_VERSION = "0.74.0"
EXPECTED_ECOSYSTEM_PREFIXES = {
    "npm": "pkg:npm/",
    "python": "pkg:pypi/",
    "dart": "pkg:pub/",
}
EXPECTED_COMPONENT_NAMES = {
    "typescript",
    "fastapi",
    "redis",
    "flutter_secure_storage",
}


def fail(message: str) -> None:
    raise SystemExit(f"sbom-evidence: {message}")


def load_json(path: Path) -> object:
    if not path.is_file():
        fail(f"missing evidence file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def trivy_versions(metadata: dict[str, object]) -> set[str]:
    tools = metadata.get("tools")
    versions: set[str] = set()
    if isinstance(tools, list):
        candidates = tools
    elif isinstance(tools, dict):
        components = tools.get("components", [])
        candidates = components if isinstance(components, list) else []
    else:
        candidates = []

    for tool in candidates:
        if not isinstance(tool, dict):
            continue
        if str(tool.get("name", "")).lower() == "trivy":
            version = str(tool.get("version", ""))
            if version:
                versions.add(version)
    return versions


def verify_sbom() -> tuple[list[dict[str, object]], dict[str, bool]]:
    data = load_json(SBOM_PATH)
    if not isinstance(data, dict):
        fail("CycloneDX report must be a JSON object")
    if data.get("bomFormat") != "CycloneDX":
        fail("SBOM report is not CycloneDX")

    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        fail("CycloneDX metadata is missing")
    versions = trivy_versions(metadata)
    if EXPECTED_TRIVY_VERSION not in versions:
        fail(
            "CycloneDX metadata does not prove the expected Trivy version "
            f"{EXPECTED_TRIVY_VERSION}; found {sorted(versions)!r}"
        )

    raw_components = data.get("components", [])
    if not isinstance(raw_components, list):
        fail("CycloneDX components must be a list")
    components = [item for item in raw_components if isinstance(item, dict)]
    if not components:
        fail("CycloneDX report contains no package components")

    names = {str(component.get("name", "")) for component in components}
    missing_names = sorted(EXPECTED_COMPONENT_NAMES - names)
    if missing_names:
        fail("expected dependency components are missing: " + ", ".join(missing_names))

    ecosystem_presence: dict[str, bool] = {}
    for ecosystem, prefix in EXPECTED_ECOSYSTEM_PREFIXES.items():
        ecosystem_presence[ecosystem] = any(
            str(component.get("purl", "")).startswith(prefix) for component in components
        )
    missing_ecosystems = sorted(name for name, present in ecosystem_presence.items() if not present)
    if missing_ecosystems:
        fail("SBOM did not detect expected ecosystems: " + ", ".join(missing_ecosystems))

    return components, ecosystem_presence


def verify_licenses() -> tuple[Counter[str], int]:
    data = load_json(LICENSE_PATH)
    if not isinstance(data, dict):
        fail("license report must be a JSON object")
    results = data.get("Results", [])
    if not isinstance(results, list):
        fail("license report Results must be a list")

    severities: Counter[str] = Counter()
    total = 0
    for result in results:
        if not isinstance(result, dict):
            continue
        licenses = result.get("Licenses", [])
        if not isinstance(licenses, list):
            continue
        for finding in licenses:
            if not isinstance(finding, dict):
                continue
            total += 1
            severity = str(finding.get("Severity", "UNKNOWN")).upper() or "UNKNOWN"
            severities[severity] += 1

    if total == 0:
        fail("license scan returned zero classified license findings")

    blocked = severities["HIGH"] + severities["CRITICAL"]
    if blocked:
        fail(
            "license scan contains blocked HIGH/CRITICAL classifications: "
            f"HIGH={severities['HIGH']} CRITICAL={severities['CRITICAL']}"
        )

    return severities, total


def main() -> None:
    components, ecosystems = verify_sbom()
    severities, license_total = verify_licenses()

    summary = {
        "source_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "trivy_version": EXPECTED_TRIVY_VERSION,
        "sbom_format": "CycloneDX",
        "component_count": len(components),
        "ecosystems": ecosystems,
        "license_finding_count": license_total,
        "license_severity_counts": dict(sorted(severities.items())),
        "blocked_license_severities": ["HIGH", "CRITICAL"],
        "known_coverage_gaps": [
            "Trivy does not provide Dart/Flutter package license scanning.",
            "Generated products and release images require release-artifact-specific SBOM/license evidence.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("SBOM/license evidence invariants: PASS")


if __name__ == "__main__":
    main()
