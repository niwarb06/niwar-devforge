# Transitive Supply-Chain Evidence

Status: CI EVIDENCE FOUNDATION — NOT A RELEASE AUTHORIZATION

This gate closes the gap between the repository's high-level third-party inventory and the exact dependencies resolved for generated products and backend runtime proofs. It creates machine-verifiable evidence for the exact Git commit being tested; it does not publish a package, container, generated application, or release.

## Evidence produced

`Supply Chain Evidence CI` regenerates the standalone Web and Flutter products from the same versioned DevForge package bundles used by the standalone distribution proof, installs their dependencies, installs the backend runtime in an isolated virtual environment, and records:

- exact source commit and tool versions;
- full and runtime Web CycloneDX SBOMs plus the exact `package-lock.json`;
- Web package-license scan output;
- exact installed backend package list, backend CycloneDX SBOM, and backend package-license scan output;
- Flutter `pubspec.lock`, full/runtime `dart pub deps --json` graphs, and a CycloneDX SBOM generated from the resolved lock state;
- a Flutter transitive license allowlist audit;
- SHA-256 checksums over every evidence file.

The workflow uploads this set as a GitHub Actions artifact named with the exact commit SHA. The CI artifact is short-lived evidence for review. A formal release must preserve the accepted evidence with the release or in another immutable retention location rather than relying on the CI retention period.

## Tooling and pinning

The gate intentionally keeps the tool set small:

- Trivy `0.74.0` is downloaded from its immutable GitHub release and the Linux x86-64 archive is verified before execution with SHA-256 `2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a`.
- CycloneDX Python `7.3.1` generates the backend SBOM from the actually installed virtual environment.
- Dart `license_checker` `1.6.2` checks the resolved Flutter dependency set against `supply-chain/flutter-license-policy.yaml`.
- `actions/upload-artifact` is pinned to reviewed commit `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (`v7.0.1`).

Adding another SBOM or license tool requires a concrete coverage gap; this workflow must not become a redundant scanner collection.

## License decision boundary

For Web and backend dependencies, Trivy's full JSON license report is preserved. The machine verifier fails closed on `UNKNOWN` or `CRITICAL` license findings. `HIGH` and `MEDIUM` findings remain visible as release-review items rather than being globally ignored because reciprocal/restricted licenses can be legitimate dependencies with specific redistribution obligations. The existing Psycopg LGPL boundary is an example: it must remain visible and be handled according to its actual redistribution terms, not hidden by a broad ignore.

For Flutter, only the small set of licenses in `supply-chain/flutter-license-policy.yaml` is permitted automatically. An unapproved/unrecognized license must fail the audit until the exact package and obligation are reviewed. Package-specific exceptions should be preferred over broadening the global allowlist when a legitimate dependency needs special treatment.

## Flutter coverage note

Trivy can generate an SBOM from Dart/Flutter lock data, but its Dart coverage does not provide package-license scanning. The Flutter evidence therefore combines four independent facts: the resolved `pubspec.lock`, full/runtime dependency graphs from Dart, a Trivy CycloneDX SBOM, and the transitive `license_checker` result. The lock/SBOM can conservatively include development dependencies; the separate `--no-dev` Dart graph records the runtime view.

## Backend reproducibility note

`packages/backend-core/pyproject.toml` currently expresses compatible dependency ranges rather than a committed production lock. The evidence job installs those ranges at the tested commit and captures the exact installed versions in both `backend-freeze.txt` and the CycloneDX environment SBOM. This is exact evidence for that CI run, but a formal repeatable release should either reuse the preserved accepted artifacts or introduce an approved lock/constraints mechanism for the released backend artifact.

## Machine verification

`scripts/verify_supply_chain_evidence.py` rejects:

- missing or empty evidence files;
- malformed or component-empty CycloneDX documents;
- malformed Trivy license reports;
- `UNKNOWN`/`CRITICAL` Web or backend license findings;
- missing tool/version markers;
- malformed source commit metadata;
- missing or mismatched SHA-256 evidence checksums.

The Flutter license command itself is fail-closed against the repository allowlist before the final evidence verifier runs.

## What this does not authorize

A green supply-chain evidence job does not authorize:

- merging PR #31 or any stacked PR;
- publishing npm/Python/Dart packages;
- publishing containers or release bundles;
- tagging a formal release;
- deploying staging or production;
- weakening branch protection or security reporting requirements.

Those remain separate repository/release decisions.
