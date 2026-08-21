# DevForge Auth Core — Phase 1 Decision

Status: DESIGN ACCEPTED FOR IMPLEMENTATION

## Objective
Provide one reusable identity/session contract that works across web, mobile, admin, and API clients without locking DevForge to a specific auth library or external provider.

## Web Default
Use a server-mediated session/BFF model:
- Browser posts credentials to a same-origin server route.
- Tokens are never returned to browser JavaScript.
- Session material is stored in Secure + HttpOnly cookies.
- Credential and logout routes are same-origin protected and `Cache-Control: no-store`.
- Protected pages revalidate after browser history restoration when required.

This design incorporates proven patterns from AI Growth Factory while removing product-specific policy.

## Mobile Default
- Mobile calls the backend/identity adapter over TLS.
- Access/refresh credentials are stored only in platform secure storage.
- Mobile auth transport is independent of web cookie transport.
- Biometric unlock may protect local credential access but never replaces server authentication.

## Domain Contract
The DevForge identity domain exposes concepts rather than library types:
- `UserIdentity`
- `Session`
- `CredentialLogin`
- `Registration`
- `RefreshSession`
- `Logout`
- `PasswordReset`
- `EmailVerification`
- `CurrentActor`
- `PermissionCheck`

## Adapter Strategy
Possible implementations can include:
- DevForge native JWT/session service
- Supabase Auth
- Firebase Auth
- OIDC/OAuth providers
- a vetted FastAPI auth library

Generated product code should depend on DevForge identity interfaces, not provider-specific SDK objects in domain logic.

## Security Defaults
- Access token lifetime is configuration/policy driven; no paid-beta/default copied from an existing product.
- Refresh credentials are independently revocable.
- Password reset/verification tokens are never logged.
- Generic public auth errors avoid unnecessary account enumeration.
- Auth responses containing sensitive state are never cached.
- Rate limiting and abuse protection are mandatory for credential and reset endpoints.
- Server-side authorization is mandatory after authentication.

## Sessions and Revocation
DevForge must support:
- per-session identifiers;
- logout/current-session revocation;
- optional all-sessions revocation;
- password-change/session invalidation policy;
- audit events for privileged authentication changes.

## Required Tests Before TRUSTED
- registration success/failure
- login success/failure
- no token leakage to web JS/public responses
- cookie flags and expiry
- same-origin/CSRF-related web protections
- refresh rotation/revocation
- logout and browser-history behavior
- password reset token secrecy
- verification token secrecy
- disabled/deleted user denial
- permission/tenant boundary tests
- rate-limit behavior

## Decision
Do not directly fork either AGF auth or Vinta auth. Build a DevForge-owned auth module using the strongest verified patterns from both, with separate web and mobile transports behind one identity contract.
