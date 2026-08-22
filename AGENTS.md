# Niwar DevForge Agent Instructions

These rules apply to every AI or automation agent working in this repository unless a narrower module instruction explicitly strengthens them.

## Before changing code

1. Read the relevant governance docs under `docs/`, especially architecture, security, module contract, AI-agent rules, quality gates, and definition of done.
2. Inspect the current branch, surrounding code, tests, migrations, and module documentation before editing.
3. Keep scope narrow. Do not mix unrelated refactors with the requested change.

## Branch and pull-request workflow

- Do not make direct changes to `main`.
- Work on a scoped feature, foundation, audit, fix, or implementation branch.
- Prefer small, reviewable commits with clear messages.
- Do not force-push, rewrite shared history, delete branches, or bypass review controls without explicit approval.
- Report exact test/check results and any remaining risk before a change is treated as complete.

## Security and data safety

- Never commit secrets, passwords, private keys, signing keys, service-role keys, VPN credentials, access tokens, production database URLs, or customer data.
- Do not weaken authentication, authorization, rate limits, audit logging, backup protections, or security checks to make tests pass.
- Do not perform destructive production data/schema actions, secret rotation, production deploys, payment configuration changes, or authorization broadening without explicit approval.
- Treat payment, wallet, KYC, identity, live-location, and other sensitive modules as high-risk and require explicit compatibility/security review.

## Reuse and external code

Use this order:

1. TRUSTED DevForge module
2. Beta/experimental DevForge module after review
3. Approved internal donor pattern
4. Approved OSS component/pattern
5. New implementation

For third-party code, preserve provenance and license notices and record the source repository, exact revision, license, maintenance/security findings, reused parts, and required attribution. Never copy proprietary, decompiled, unknown-license, or unreviewed sensitive code into DevForge.

## Contracts, migrations, and compatibility

- Keep reusable domain contracts provider-neutral and product-neutral.
- Prefer typed/versioned API contracts and generated clients over duplicated handwritten schemas.
- Database changes must use migrations.
- Schema/API/session/auth changes require backward-compatibility and rollback review.
- Do not mutate existing migration history after it has been shared or released unless explicitly approved.

## Testing and quality

Run the checks required by the changed module. At minimum, do not claim completion without reporting applicable lint/static analysis, type checks, tests, migration validation, security checks, and build results.

Generated or AI-written code is not automatically trusted. It must satisfy the same quality gates as human-written code.

## Documentation

Update module contracts, configuration examples, migration/upgrade notes, and architecture decisions when behavior or public interfaces change. Never put real credentials into examples; use placeholders only.

## Escalate instead of guessing

Stop and request explicit approval when a task requires destructive production changes, secret rotation, production deployment, broad authorization changes, payment/KYC security decisions, unapproved licenses, history rewriting, or disabling a required safety/quality control.
