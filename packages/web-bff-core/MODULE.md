# Web BFF Core Module

- Name: web-bff-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: Next.js/web products using standard Route Handlers

## Purpose

Provides the reusable browser authentication boundary for DevForge web products while keeping opaque backend session credentials out of browser JavaScript.

## Public interface

- `createWebAuthBff(config)`
- `WebBffConfig`
- `WebAuthBffHandlers`
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

## Configuration

- `backendApiBaseUrl`: backend API prefix such as `https://api.example.com/api/v1`
- `publicOrigin`: exact browser origin such as `https://app.example.com`
- `cookieName`: optional; defaults to `__Host-devforge_session`
- `secureCookie`: optional; defaults to `true`
- `maxRequestBodyBytes`: optional; defaults to 16 KiB
- `fetchImpl`: optional adapter for runtime/testing

For HTTP localhost only, a non-`__Host-` cookie name may be paired with `secureCookie: false`. Staging/production must use secure cookies.

## Current limitations / promotion blockers

- trusted proxy/client-address policy is still required before production BFF credential traffic can preserve meaningful per-client backend rate limiting
- browser history restoration/revalidation behavior needs an application integration proof
- no full generated Next.js application pilot yet
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
