# Web Session Core

`@niwar-devforge/web-session-core` is the browser-side companion to `web-bff-core`. It revalidates authenticated UI state against the same-origin BFF without ever reading or storing the opaque backend bearer session.

Status: **EXPERIMENTAL**.

## Why it exists

Browser back/forward navigation can restore a page from the back-forward cache (BFCache) with JavaScript memory and rendered authenticated UI from an earlier moment. A user may have logged out, been disabled, or had a session revoked after that snapshot was created. Protected UI must therefore revalidate before trusting restored session state.

## Core behavior

- default session endpoint: `/api/auth/me`
- endpoint must be root-relative and same-origin; absolute/protocol-relative/query/fragment forms are rejected
- requests use `GET`, `credentials: "same-origin"`, `cache: "no-store"`, and `redirect: "error"`
- no `Authorization` header or bearer token is created or exposed in browser JavaScript
- `pageshow` triggers revalidation; BFCache restores (`event.persisted === true`) are identified as `bfcache`
- `visibilitychange` triggers revalidation only when the document becomes visible
- `start()` performs an initial revalidation by default
- `revalidate("auth-change")` is provided for login/logout/profile-auth transitions
- every refresh enters `checking` before a result is trusted, allowing products to hide or gate stale protected UI
- `401` becomes `anonymous`
- transient/non-401 failures become a sanitized `error` state rather than falsely treating the user as logged out
- response bodies are bounded (64 KiB default, configurable 1 KiB–256 KiB)
- newer revalidations invalidate/abort older requests so stale responses cannot overwrite fresher auth state

## Minimal usage

```ts
import { createWebSessionMonitor } from "@niwar-devforge/web-session-core";

const monitor = createWebSessionMonitor({
  onChange(snapshot) {
    // Render protected content only after a fresh authenticated snapshot.
    updateAuthState(snapshot);
  },
});

monitor.start();

// After a successful same-origin BFF login/logout action:
await monitor.revalidate("auth-change");

// On component/app teardown:
monitor.stop();
```

A generated React/Next.js wrapper may adapt the snapshots to a store or context, but this package deliberately has no React or Next.js runtime dependency.

## Security boundary

This module is browser-safe state orchestration only. It does not own credentials. Browser code must authenticate through `web-bff-core`/same-origin route handlers where the opaque backend token remains in a Secure + HttpOnly cookie and is translated to bearer server-side.

Do not replace the same-origin BFF endpoint with a direct backend bearer endpoint. Do not put session tokens in localStorage, sessionStorage, IndexedDB, URLs, React state, logs, or browser-visible JSON.

## Promotion requirements

Before promotion from EXPERIMENTAL, prove the module in a real generated Next.js product with browser automation covering login, logout, BFCache/back-forward restoration where supported, revoked/disabled sessions, transient upstream failure, and protected-UI gating while `checking`.
