# Contributing to Niwar DevForge

Thanks for helping improve Niwar DevForge. The project favors small, reviewable, tested changes that preserve reusable module boundaries and security guarantees.

## Before contributing

1. Read `AGENTS.md` and the relevant governance/module documentation under `docs/`.
2. Search existing issues and pull requests before starting overlapping work.
3. Keep product-specific assumptions out of reusable core modules.
4. Never submit secrets, private keys, production credentials, customer data, or proprietary material you do not have the right to contribute.

## Development workflow

- Create a scoped branch; do not work directly on `main`.
- Keep commits focused and explain security, compatibility, migration, and rollback implications when applicable.
- Add or update tests for behavior changes and regressions.
- Run the checks required by the affected module, including relevant format/lint, type/static analysis, tests, build, migration, dependency, and security gates.
- Update public contracts and documentation when behavior or interfaces change.

## External code and dependencies

Third-party code is not accepted by copy/paste alone. Follow `docs/03_OSS_INTAKE_POLICY.md`: record provenance, exact revision/version, license, required notices, maintenance/security findings, and why reuse is justified. Do not submit code with an unknown, incompatible, proprietary, or unreviewed license.

## Licensing of contributions

Niwar DevForge is licensed under the Apache License, Version 2.0. Unless you conspicuously state otherwise and the maintainers explicitly accept different terms, any contribution intentionally submitted for inclusion in the project is submitted under Apache-2.0 as described by Section 5 of that license.

By submitting a contribution, you represent that you have the right to do so and that required third-party notices and license obligations have been preserved.

## Security reports

Do not disclose vulnerabilities publicly. Follow `SECURITY.md` and use GitHub private vulnerability reporting when available.

## Review

A pull request is not considered complete merely because it builds. Maintainers may require security review, provenance/license review, compatibility proof, migration/rollback evidence, or additional tests before accepting a change.
