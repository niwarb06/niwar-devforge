# Security Policy

Niwar DevForge treats security reports as sensitive until a fix and disclosure plan are ready.

## Reporting a vulnerability

Please use GitHub's private **Report a vulnerability** flow for this repository when it is available under the Security tab.

If private vulnerability reporting is not available, contact the repository maintainer through GitHub first and request a private reporting channel. Do **not** place exploit details, credentials, private keys, production endpoints, customer data, or proof-of-concept payloads in a public issue, discussion, pull request, or comment.

For a useful report, include the affected module/version or commit, impact, prerequisites, minimal reproduction steps, and any suggested mitigation. Redact secrets and personal data.

## Scope

Security reports are welcome for DevForge-owned source code, generated-product templates, authentication/session behavior, authorization, staging/release tooling, dependency and supply-chain controls, and documented security boundaries.

Third-party vulnerabilities should also be reported to the relevant upstream project when appropriate. DevForge will track affected dependency versions and mitigations without claiming ownership of upstream fixes.

## Response and disclosure

Maintainers will validate reports, assess severity and affected versions, prepare remediation and regression coverage, and coordinate disclosure when practical. No service-level response time is promised while the project remains under active development.

## Safe handling

Do not test against systems or data you do not own or have explicit permission to test. Do not exfiltrate data, degrade availability, or retain sensitive information beyond what is necessary to demonstrate the issue.
