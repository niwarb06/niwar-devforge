# Module: Web Session Core

## Status

EXPERIMENTAL

## Purpose

Provide a reusable, framework-neutral browser session lifecycle that prevents cached/restored authenticated UI from being trusted without a fresh same-origin BFF session check.

## Public contract

The module exports:

- `createWebSessionMonitor<TProfile>(config)`
- `WebSessionMonitor<TProfile>`
- `WebSessionSnapshot<TProfile>`
- `WebSessionStatus`
- `WebSessionSource`

Session states are `idle`, `checking`, `authenticated`, `anonymous`, and `error`.

## Required security properties

1. The session-check endpoint is root-relative and same-origin only.
2. Browser session checks never construct, read, log, or persist backend bearer tokens.
3. Fetch uses same-origin credentials, no-store caching, and redirect rejection.
4. A revalidation emits `checking` before a restored/cached authenticated state can be trusted.
5. BFCache `pageshow` restores trigger a fresh session check.
6. Returning to a visible document triggers a fresh session check.
7. `401` maps to anonymous; other failures map to a generic error state so transient outages are not confused with logout.
8. Response payloads are bounded before JSON decoding.
9. Older in-flight checks cannot overwrite a newer auth decision.
10. Event listeners and in-flight work are removable/abortable through `stop()`.

## Integration contract

Web products pair this package with the server-only `@niwar-devforge/web-bff-core` route-handler adapter. The browser endpoint normally maps to BFF `me()`, which reads the HttpOnly cookie server-side and translates it to backend bearer auth. Browser code receives profile/auth state only.

Generated UI must treat `checking` as untrusted for protected content. Products may render a neutral loading shell, but must not display sensitive cached account data while a BFCache/session refresh is unresolved.

After successful login/logout or another authentication-changing action, products should call `revalidate("auth-change")` rather than manually assuming the next auth state.

## Compatibility

- TypeScript 5.9.2
- modern browser Web Fetch/AbortController/TextDecoder APIs
- standard browser `pageshow` and `visibilitychange`
- no React/Next.js runtime dependency
- import has no browser-global side effects; default globals are resolved when a monitor is created

## Integration evidence

`apps/web_next` is the first real Next.js + Chromium reference integration. Its deterministic browser suite verifies login/logout, HttpOnly credential isolation, server-side revocation followed by browser back navigation, explicit BFCache-style `pageshow` revalidation, disabled-user rejection, and protected-DOM fail-closed behavior while session trust is being refreshed.

A second Chromium suite runs the same browser session contract through the real BFF into FastAPI `backend-core` backed by PostgreSQL and Redis. That suite verifies authenticated state after real registration/login, profile reads and updates through the BFF, protected rendering, logout, cookie clearing, and continued token non-exposure with the simulator disabled.

The reference therefore proves both the framework/browser lifecycle contract and real reusable-backend CI integration. It does not yet prove a production ingress/deployment topology.

## Tests / quality gate

The module must pass:

- strict TypeScript typecheck
- compiled Node test suite
- same-origin request-options regression
- BFCache pageshow regression
- visible-document regression
- 401 vs transient-failure mapping
- stale-request ordering regression
- bounded-body regression
- listener teardown regression
- real Chromium reference-pilot coverage for protected history restoration and auth lifecycle
- real-backend Chromium coverage against FastAPI `backend-core`, PostgreSQL, and Redis

## Promotion gates

The real-browser Next.js reference integration and real `backend-core` CI path are now covered. Promotion to BETA/TRUSTED still requires production-like BFF/ingress deployment evidence, exact trusted-proxy topology proof, generator-produced product proof, broader lifecycle/failure-path evidence in that environment, and repeated product reuse required by the DevForge module contract.
