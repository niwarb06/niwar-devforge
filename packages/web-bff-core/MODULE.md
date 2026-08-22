# Web BFF Core Module

- Name: web-bff-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: Next.js/web products using standard Route Handlers

## Purpose

Provides the reusable browser authentication boundary for DevForge web products while keeping opaque backend session credentials out of browser JavaScript and supporting an explicit trusted client-address adapter for credential abuse controls.

## Public interface

- `createWebAuthBff(config)`
- `WebBffConfig`
- `WebAuthBffHandlers`
- `TrustedClientAddressResolver`
- handlers: `register`, `login`, `logout`, `me`, `updateProfile`

## Security contract

- login/register/logout/profile mutation require an exact configured same-origin `Origin` value
- `Sec-Fetch-Site`, when present, must be `same-origin`
- browser session state is stored in a host-only `Secure` + `HttpOnly` + `SameSite=Lax` cookie
- default cookie name is `__Host-devforge_session`
- cookie path is `/`; no Domain attribute is emitted
- backend session token is never included in the browser login response body
- backend calls use server-side `Authorization: Bearer` translation
- stale 401 sessions clear the browser cookie
- logout attempts backend revocation and always clears the local cookie on handled outcomes
- credential/profile mutation bodies must be JSON and are bounded to 16 KiB by default
- sensitive BFF responses are `no-store`
- unexpected upstream failures are replaced with generic public errors
- browser-provided `X-Forwarded-For` is not relayed by default
- a configured `resolveTrustedClientAddress` may return exactly one IPv4/IPv6 literal from trusted server/platform metadata; invalid or multi-value output fails closed before backend fetch

## Configuration

- `backendApiBaseUrl`: backend API prefix such as `https://api.example.com/api/v1`
- `publicOrigin`: exact browser origin such as `https://app.example.com`
- `cookieName`: optional; defaults to `__Host-devforge_session`
- `secureCookie`: optional; defaults to `true`
- `maxRequestBodyBytes`: optional; defaults to 16 KiB
- `resolveTrustedClientAddress`: optional server-only deployment adapter for a trustworthy client IP; never blindly copy a browser header
- `fetchImpl`: optional adapter for runtime/testing

For HTTP localhost only, a non-`__Host-` cookie name may be paired with `secureCookie: false`. Staging/production must use secure cookies.

The backend must separately configure only the real BFF/proxy network ranges in `DEVFORGE_TRUSTED_PROXY_CIDRS`. See `docs/17_TRUSTED_PROXY_CLIENT_ADDRESS.md`.

Browser history/session restoration orchestration lives separately in `@niwar-devforge/web-session-core`. Keeping that browser-safe package separate prevents server-only BFF configuration and credential-translation code from being bundled into client UI code.

## Integration evidence

`apps/web_next` provides a real Next.js + Chromium reference proof that composes this package with `web-session-core`. The pilot verifies browser-safe login/logout/me route handlers, HttpOnly-cookie behavior, absence of the opaque session token from browser-visible responses/storage/DOM, protected-content gating, server-side session revocation followed by browser back navigation, and disabled-user revalidation.

The pilot uses an explicitly gated in-process backend simulator for deterministic CI; it is integration evidence only and is not production-backend evidence.

## Current limitations / promotion blockers

- each production topology must prove ingress forwarding-header sanitization and exact BFF/proxy CIDR ownership/configuration
- real `backend-core` integration behind the BFF still needs production-like evidence
- a generator-produced product pilot and repeated product reuse are still required for higher maturity
- no production-like deployment evidence yet

The package must not be promoted to TRUSTED until those items are closed and the module contract quality gates are met.

## Tests and gates

CI must verify:

- strict TypeScript compilation
- login token is absent from response body
- Secure/HttpOnly/SameSite/Path cookie flags
- cross-origin credential rejection before backend fetch
- server-side bearer translation for profile reads
- stale-session cookie clearing
- backend logout revocation call plus cookie clearing
- `__Host-`/Secure invariant
- JSON content-type enforcement
- browser-supplied forwarding metadata is not relayed by default
- trusted client-address resolver emits one validated IP when explicitly configured
- invalid/multi-value resolver output fails closed before backend fetch
- the Next.js browser pilot remains green for login/logout, history revocation, token non-exposure, and disabled-user behavior
