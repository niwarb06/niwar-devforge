# DevForge Next.js Browser Auth Pilot

Status: **EXPERIMENTAL reference app**.

This app is the real-browser integration proof for the reusable `web-bff-core` and `web-session-core` packages. It is intentionally small and product-neutral.

## What it proves

- Next.js App Router route handlers can wrap `web-bff-core` without exposing opaque backend session tokens to browser JavaScript.
- Browser auth state is revalidated through `/api/auth/me` using `web-session-core`.
- Protected UI is hidden unless the latest browser session snapshot is authenticated.
- Back/forward navigation and BFCache-style `pageshow` restoration force session revalidation.
- Server-side revocation is reflected in the browser before restored protected content is trusted.
- Logout clears the HttpOnly browser cookie and revalidates the client state.

## Pilot-only backend

`/api/pilot-backend/v1/*` is an in-process contract simulator used only by this reference app and E2E tests. It is **not** a substitute for `backend-core`, PostgreSQL, Redis, production rate limiting, or deployment proof.

The test-control route is disabled unless `DEVFORGE_PILOT_TEST_CONTROL=1` and also requires the fixed CI-only header used by the Playwright suite.

## Local proof

Build the reusable web packages first, install this app, then run:

```bash
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Default local origin: `http://127.0.0.1:3000`.

## Security boundary

- No bearer token is stored in localStorage, sessionStorage, IndexedDB, URLs, React state, or browser-visible JSON.
- The browser cookie is HttpOnly and SameSite=Lax.
- Local HTTP uses a non-`__Host-` cookie only for this development proof. Production must use the secure BFF cookie contract.
- Protected DOM is fail-closed by a document-level trust marker in addition to React state, so a restored DOM snapshot is hidden synchronously when revalidation begins.

## Remaining promotion work

This pilot closes the real Next.js/browser integration gap. Promotion of the web auth foundation to TRUSTED still requires production-like ingress/BFF deployment evidence, real backend integration, and the broader module promotion gates documented by DevForge.
