# Trivy SBOM / License Evidence Intake

Status: ADOPT FOR ISOLATED CI EVIDENCE; NOT A COMPLETE LICENSE-CLEARANCE SYSTEM

## Candidate

- Repository: `aquasecurity/trivy`
- Adopted release: `v0.74.0`
- Release commit: `e1fd17a0ea4a8cf24bc4b4dd7e2cfbf4bb31b994`
- License: Apache-2.0
- Runtime form used by DevForge CI: official GHCR image pinned to the reviewed Linux/amd64 digest, never `latest` and never a mutable tag alone.

## Why this is useful

Trivy gives DevForge one reusable machine-readable supply-chain evidence layer for:

- CycloneDX SBOM generation from repository/filesystem content;
- transitive dependency discovery across supported language package managers;
- package and source license classification where Trivy has coverage;
- vulnerability/security scanning in later release gates without inventing a custom scanner.

This materially reduces custom CI code and fits the DevForge reuse-first policy.

## Security review

Trivy experienced a supply-chain compromise in March 2026. Malicious Trivy artifacts and action tags were published during a bounded exposure window. The project advisory states that digest-pinned images are not affected by tag replacement and that releases from the immutable-release era can be safely pinned and verified.

DevForge therefore does **not** use `aquasecurity/trivy-action`, `aquasecurity/setup-trivy`, `latest`, or an unpinned Trivy container in this gate.

The CI execution boundary is additionally hardened:

1. pull the official image by exact digest;
2. mount the checked-out repository read-only;
3. give Trivy no GitHub token or repository credentials;
4. run the scan container with `--network=none` after the image pull;
5. run as the host runner UID/GID;
6. drop all Linux capabilities and set `no-new-privileges`;
7. mount only a dedicated evidence directory read-write for reports;
8. keep checkout credentials disabled with `persist-credentials: false`.

This sharply limits exfiltration or workspace mutation even if a scanner image were later found to be malicious.

## Maintenance / maturity

`v0.74.0` was released in August 2026 and is an immutable GitHub release. Trivy remains actively maintained and supports SBOM generation for Node.js, Python, and Dart package ecosystems used by DevForge.

Decision: **ADOPT** as an isolated CI evidence tool with immutable provenance controls.

## Coverage boundary

This gate is deliberately not represented as a complete legal clearance system.

- npm: SBOM and license detection are supported; installed package metadata is materialized before scanning.
- Python: SBOM coverage is supported. License coverage depends on package/install metadata; the gate materializes the backend runtime into a dedicated scan directory.
- Dart/Flutter: SBOM coverage from `pubspec.lock` is supported, including transitive dependencies, but Trivy does not currently provide Dart package license scanning.
- Generated products and release container images must still receive their own exact release-artifact SBOM/license evidence when they are independently published.

Therefore a passing gate means:

- a machine-readable SBOM was produced and validated;
- expected npm/Python/Dart ecosystems were detected;
- Trivy-reported HIGH/CRITICAL license classifications are absent;
- remaining reciprocal/unknown license findings are explicitly summarized for review.

It does **not** mean every transitive Flutter/Dart license has been legally cleared.

## Upgrade rule

Any Trivy version or image-digest change requires a new OSS intake review covering:

- release/tag provenance;
- immutable artifact/digest verification;
- security advisories since the pinned release;
- command/coverage changes;
- exact new image digest;
- CI evidence on the new exact DevForge head.
