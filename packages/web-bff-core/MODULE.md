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

## Browser pilot evidence

`apps/web_next` now composes this package with `web-session-core` through real Next.js App Router Route Handlers and Chromium/Playwright. The pilot verifies that browser login JSON does not contain the opaque session token, the cookie is HttpOnly, logout revokes/clears the session, back/history restoration revalidates before protected UI is trusted, disabled sessions become anonymous, and transient upstream failure is not misclassified as logout.

The pilot uses a loopback test backend and an explicit localhost-only non-Secure cookie exception. It does not replace the production Secure `__Host-devforge_session` contract.

## Current limitations / promotion blockers

- each production topology must prove ingress forwarding-header sanitization and exact BFF/proxy CIDR ownership/configuration
- the real Next.js browser reference pilot is complete, but a generator-produced product pilot is still required
- production-like TLS + real backend/PostgreSQL/Redis integration evidence is still required
- operational monitoring, rollback, and deployment evidence remain open

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
- Next.js browser pilot exercises login/logout/history revalidation and protected-content gating
