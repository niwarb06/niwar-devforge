# Niwar DevForge — Open-Source Intake Policy

## Purpose
Use open-source software to accelerate delivery without importing hidden legal, security, maintenance, or architecture debt.

## Required checks before reuse
Every candidate repository/component must record:
1. Exact repository and commit/tag.
2. License and obligations.
3. Last meaningful maintenance activity.
4. Runtime/framework versions and dependency freshness.
5. Known vulnerabilities and secret exposure.
6. Architecture fit and code quality.
7. Test coverage/CI evidence.
8. Whether it is demo/UI-only, MVP-quality, or production-oriented.
9. Amount of modification needed.
10. Decision: adopt, adapt, reference only, or reject.

## License preference
Preferred for reusable commercial foundations when compatible with the dependency tree:
- MIT
- Apache-2.0
- BSD-2-Clause / BSD-3-Clause

Licenses with reciprocal/network-copyleft obligations such as GPL/AGPL require explicit legal/architecture review before use in DevForge or commercial products.

## Security rules
Never reuse:
- Embedded private keys, credentials, API secrets, signing keys, or production endpoints with secrets.
- Authentication/authorization code that has not been independently reviewed.
- Payment, wallet, KYC, cryptography, or security-sensitive implementations solely because they are available as a template.

## Reuse hierarchy
Prefer in this order:
1. Well-maintained library/package with clear API and license.
2. Well-maintained reference implementation.
3. Isolated reusable component.
4. Full application template only when architecture and license justify it.
5. UI/flow reference only for old or demo repositories.

## Provenance
Preserve required copyright/license notices and maintain a third-party inventory for every DevForge release.

## No blind copy rule
Open source shortens implementation time; it does not eliminate verification. All imported code must pass DevForge tests, security checks, formatting, documentation, and module boundaries before becoming trusted reusable code.
