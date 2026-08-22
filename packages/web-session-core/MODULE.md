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

## Browser pilot evidence

`apps/web_next` now provides a real Next.js App Router + Chromium/Playwright reference pilot. It verifies same-origin BFF login, HttpOnly token isolation, logout/revocation, protected-content gating while `checking`, back/history revalidation after a user is disabled, and transient upstream failure mapping. The pilot uses a test-only HTTP backend so it is integration evidence, not production deployment approval.

## Promotion gates

The real-browser reference integration gate is satisfied at the EXPERIMENTAL level. Promotion to BETA/TRUSTED still requires a generator-produced product pilot plus production-like BFF/backend deployment evidence covering TLS, trusted proxy topology, real PostgreSQL/Redis-backed auth/session behavior, rollback/monitoring, and supported browser history/BFCache behavior.
