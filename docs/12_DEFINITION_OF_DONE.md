# Niwar DevForge — Definition of Done

A task is not Done merely because code exists or a screen works once.

## Feature Done
- Acceptance criteria are satisfied.
- Happy path and relevant failure/empty/loading states work.
- Authorization and validation are enforced at the correct boundary.
- Tests cover important behavior and regressions.
- Logs/errors do not expose sensitive data.
- User-facing strings are localizable; ku/ar/en and RTL/LTR are verified when required.
- Documentation/configuration is updated.
- No unresolved blocker-level security or data-integrity issue remains.

## Reusable Module Done
All Feature Done criteria plus:
- Product-neutral naming and behavior.
- No product-specific secrets, domains, identifiers, branding, or business data.
- Public contract/interface documented.
- Provider dependencies isolated behind adapters where appropriate.
- Version recorded and changelog/migration notes added for breaking changes.
- Independent tests pass.
- Module status may be promoted to TRUSTED only after reuse-quality review.

## Product Pack Done
- Pack declares required and optional modules.
- Pack-specific domain model and workflows are documented.
- At least one reference implementation/test flow proves assembly works.
- Security/privacy risks unique to the product family are documented.

## Production Candidate Done
- Build/static checks pass.
- Required unit/integration/e2e tests pass.
- Security/dependency/secret checks pass or have approved dispositions.
- Migrations have rollback/backup strategy where needed.
- Staging validation completed.
- Monitoring and health checks are ready.
- Release notes and rollback procedure exist.
- Production deployment is explicitly approved.

## DevForge Phase Done
A DevForge phase is complete only when its exit criteria are evidenced in repository files, tests, or working artifacts—not only described in chat.
