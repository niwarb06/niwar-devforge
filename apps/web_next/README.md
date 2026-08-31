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
- A disabled user is rejected by the next browser session check.
- A second CI proof runs the browser BFF against the real FastAPI `backend-core` with PostgreSQL and Redis instead of the simulator.

## Pilot-only backend

`/api/pilot-backend/v1/*` is an in-process contract simulator used by the deterministic browser lifecycle suite. It is **not** a substitute for `backend-core`, PostgreSQL, Redis, production rate limiting, or deployment proof.

In development the simulator is available for local proof. Under `NODE_ENV=production` it returns 404 unless `DEVFORGE_PILOT_INPROCESS_BACKEND=1` is explicitly set. The test-control route additionally requires `DEVFORGE_PILOT_TEST_CONTROL=1` and the fixed CI-only header used by the Playwright suite.

The real-backend suite deliberately leaves the simulator disabled and points `DEVFORGE_PILOT_BACKEND_API_BASE_URL` at a separate FastAPI process using migrated PostgreSQL plus Redis credential-abuse controls.

Production-mode startup requires explicit `DEVFORGE_PILOT_PUBLIC_ORIGIN` and `DEVFORGE_PILOT_BACKEND_API_BASE_URL`; it never silently falls back to localhost configuration.

## Local proof

Build the reusable web packages first, install this app, then run the deterministic simulator suite:

```bash
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

The real-backend proof additionally requires `backend-core` installed, its migrations applied to PostgreSQL, Redis available, and these endpoints configured before running:

```bash
npm run test:e2e:real-backend
```

Default local browser origin: `http://127.0.0.1:3000`. The real backend proof defaults to `http://127.0.0.1:8000/api/v1`.

## Real backend evidence

The real-backend Chromium suite verifies the actual reusable path:

`Browser -> Next.js BFF -> FastAPI backend-core -> PostgreSQL / Redis`

It exercises registration, login, current-profile read, profile update, protected-page access, and logout. It also verifies the in-process simulator is disabled, the browser login response contains no session token, the opaque session cookie is HttpOnly, and browser storage/DOM do not expose the backend credential.

This is CI integration evidence, not production ingress evidence. It does not prove TLS termination, reverse-proxy header sanitization, production secret delivery, horizontal scaling, backup/rollback operations, or a real deployed topology.

## Security boundary

- No bearer token is stored in localStorage, sessionStorage, IndexedDB, URLs, React state, or browser-visible JSON.
- The browser login response is consumed and must contain `authenticated: true`; any browser-visible `session_token` field is rejected.
- The browser cookie is HttpOnly and SameSite=Lax.
- Local HTTP uses a non-`__Host-` cookie only for these development/CI proofs. Production products must use the secure BFF cookie contract.
- Protected DOM is fail-closed by a document-level trust marker in addition to React state, so a restored DOM snapshot is hidden synchronously when revalidation begins.
- The in-process simulator and its fixed pilot credentials are test/reference infrastructure only and must not be deployed as an application backend.

## Remaining promotion work

The reference now covers both real Chromium lifecycle behavior and real `backend-core` + PostgreSQL + Redis integration in CI. Promotion of the web auth foundation to TRUSTED still requires production-like ingress/BFF deployment evidence, exact trusted-proxy topology proof, generator-produced product proof, broader lifecycle/failure-path evidence in that environment, and repeated product reuse under the DevForge module contract.
