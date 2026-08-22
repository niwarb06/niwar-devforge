# DevForge Next.js Web Auth Pilot

Status: **EXPERIMENTAL reference application**.

This app is the first runnable `apps/web_next` proof that composes the server-only `@niwar-devforge/web-bff-core` with the browser-safe `@niwar-devforge/web-session-core` in a real Next.js App Router application.

## What this pilot proves

- browser login goes through a same-origin Next.js Route Handler and the BFF
- the opaque backend session stays in an HttpOnly cookie and is absent from browser-visible login JSON
- browser JavaScript never constructs or stores a bearer token
- logout revokes the backend session and clears the browser cookie
- protected UI is hidden while session state is `checking`
- back/history navigation forces session revalidation before restored protected UI can be trusted
- a disabled/revoked session becomes anonymous after revalidation
- a transient backend failure becomes a sanitized `error` state rather than being mistaken for logout
- Chromium browser automation exercises the integration end to end

## Test topology

The browser talks only to `http://127.0.0.1:4100`. Next.js Route Handlers use `web-bff-core` to call a small test-only HTTP backend on `127.0.0.1:4101`. The fake backend exists only under `tests/support` and provides deterministic session lifecycle controls for browser tests.

The local test topology explicitly enables an insecure localhost cookie exception with `DEVFORGE_PILOT_ALLOW_INSECURE_LOCALHOST=1`. The server adapter rejects that exception for non-loopback public origins. Production/staging must use the default Secure `__Host-devforge_session` cookie contract.

## CI contract

The pilot CI builds both reusable web auth packages, builds this Next.js app, installs Chromium for Playwright, then runs the browser suite. Direct package versions are exact-pinned; a repository-wide lockfile policy for reusable/app packages remains a separate reproducibility hardening item.

## Not production approval

This proves the browser/application lifecycle but does not by itself promote the web auth modules to TRUSTED. Production-like deployment evidence is still required for TLS, ingress/header sanitization, trusted proxy CIDRs, real backend/Redis/PostgreSQL integration, and final operational monitoring/rollback behavior.
