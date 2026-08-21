# Niwar DevForge — Security Baseline

This baseline applies to every generated or reusable DevForge product unless a stricter product-specific policy overrides it.

## 1. Secrets
- No production secret, private key, token, password, signing key, VPN credential, service-role key, or database credential may be committed.
- Repositories contain only `.env.example` files with non-secret placeholders.
- Secrets must come from an approved secret store or deployment environment.
- Secret scanning is a release gate.

## 2. Authentication and Sessions
- Use short-lived access tokens and secure refresh/session handling.
- Store mobile secrets/tokens only in platform secure storage.
- Web auth cookies must be Secure, HttpOnly, and SameSite-appropriate.
- Sensitive account actions require recent authentication where practical.
- Passwords are never logged or stored in plaintext.

## 3. Authorization
- Every protected operation is authorized server-side.
- Client-side role checks are UX only, never the security boundary.
- Default-deny for privileged actions.
- Admin, owner, staff, and user roles must have explicit permissions.
- Multi-tenant data access must always include tenant/workspace boundaries.

## 4. API and Input Safety
- Validate and normalize all untrusted input.
- Use typed request/response contracts.
- Apply rate limits to authentication, messaging, search abuse, payments, uploads, and public endpoints as appropriate.
- Never trust client-supplied price, role, ownership, verification, or payment state.
- Use idempotency for payment and other retry-sensitive writes.

## 5. Database
- Migrations are versioned and reviewable.
- Destructive migrations require explicit approval and rollback/backup planning.
- Database accounts follow least privilege.
- Row-level security is required where the chosen architecture relies on direct client access.
- Financial/wallet records use append-oriented ledger semantics rather than mutable balances alone.

## 6. Files and Media
- Validate file size, type, and ownership.
- Use signed/private access for sensitive uploads.
- Never expose identity documents or private media through predictable public URLs.
- Strip or deliberately handle metadata when privacy matters.

## 7. Payments and Verification
- Payment success is confirmed server-side through trusted provider responses/webhooks.
- Webhooks must be authenticated/verified and idempotent.
- Card data must not pass through DevForge systems unless explicitly designed for PCI scope.
- KYC/identity data is treated as highly sensitive and access is audited.

## 8. Mobile and Web Transport
- HTTPS/TLS is mandatory in production.
- Cleartext traffic is disabled unless a documented local-development exception exists.
- API keys shipped to clients must be public/restricted keys; private credentials never ship in apps.
- High-risk public API keys should be restricted by package/bundle/domain/API scope where the provider supports it.

## 9. Logging and Privacy
- Never log passwords, access tokens, refresh tokens, private keys, full payment credentials, or raw identity documents.
- Sensitive fields are redacted.
- Security-relevant admin and privileged actions generate audit events.
- Data retention must be deliberate and documented.

## 10. Dependencies and Open Source
- Lock dependency versions.
- Run dependency vulnerability checks in CI.
- No open-source code enters the reusable core without license and security review.
- Unmaintained dependencies need an explicit exception or replacement plan.

## 11. CI/CD and Production
- Pull-request checks must pass before protected-branch merge.
- Build artifacts are reproducible from repository state and controlled secrets.
- Staging is required before production for material changes.
- Production deployment requires rollback capability.
- Backups must be tested, not merely configured.

## 12. AI Agent Guardrails
AI agents may inspect, scaffold, implement, test, and prepare changes, but must not autonomously:
- expose or rotate real secrets without explicit authorization;
- delete production data;
- weaken authentication/authorization;
- disable security checks to make CI pass;
- deploy payment/security-sensitive changes directly to production;
- import code with unknown or incompatible licensing.

## Release Security Gate
A production candidate is blocked by any known Critical/High vulnerability that is exploitable in the product context, committed secret, broken authorization path, unverified payment path, or missing rollback for a destructive migration.
