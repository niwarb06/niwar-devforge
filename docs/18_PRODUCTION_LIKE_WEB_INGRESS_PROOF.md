# Production-like Web Ingress Proof

Status: IMPLEMENTATION / CI EVIDENCE — NOT A PRODUCTION DEPLOYMENT

## Purpose

Close the next web-auth integration gap after the real-backend Chromium pilot by exercising the reusable browser/BFF/backend path behind a TLS-terminating ingress boundary with explicit forwarding-header sanitization.

This proof is intentionally provider-neutral and CI-only. It does not deploy to staging or production and does not use real secrets, certificates, domains, customer data, or production infrastructure.

## Proven topology

```text
Chromium
  -> HTTPS ingress harness (TLS 1.2+)
     -> Next.js App Router / web BFF on loopback
        -> FastAPI backend-core on loopback
           -> PostgreSQL
           -> Redis
```

The public browser origin is `https://127.0.0.1:3443` for CI. The certificate is an ephemeral one-day self-signed certificate generated at runtime with OpenSSL and deleted when the ingress process exits.

## Forwarding-header contract

The ingress harness removes inbound values for:

- `Forwarded`
- `X-Forwarded-For`
- `X-Forwarded-Host`
- `X-Forwarded-Proto`
- `X-Real-IP`
- `X-DevForge-Ingress-Client-IP`

It then derives the peer address from the TLS connection and writes sanitized forwarding metadata, including one deployment-private `X-DevForge-Ingress-Client-IP` value for the reference BFF adapter.

The Next.js pilot enables that adapter only when:

```text
DEVFORGE_PILOT_TRUST_INGRESS_CLIENT_IP=1
```

Trusted-ingress mode also requires an HTTPS public origin. The default remains disabled.

The reusable `web-bff-core` still performs IP-literal validation and emits a single `X-Forwarded-For` value only on credential requests.

For this host-local CI topology, backend-core is configured with the narrow trust range:

```text
DEVFORGE_TRUSTED_PROXY_CIDRS=["127.0.0.1/32"]
```

## Browser evidence

The production-like Chromium suite verifies:

1. the browser is using the HTTPS public origin;
2. three registration attempts carry three different spoofed browser forwarding-header values;
3. ingress sanitization causes those requests to remain in one backend client-IP rate-limit bucket, so the configured two-request IP limit returns `429` on the third request;
4. login succeeds through ingress -> BFF -> real backend;
5. the session token is not returned to browser-visible JSON;
6. the session cookie is `HttpOnly`, `Secure`, and `SameSite=Lax`;
7. the session token is absent from `document.cookie`, localStorage, sessionStorage, and rendered HTML;
8. protected rendering and logout still work through the TLS topology.

## CI quality gates

`.github/workflows/web-production-like-ingress-ci.yml` performs:

- PostgreSQL and Redis service health checks;
- web BFF build;
- web session build;
- backend-core installation;
- Alembic migration to head;
- Next.js dependency install;
- TypeScript check;
- production Next.js build;
- Chromium install;
- production-like TLS ingress browser E2E.

No new runtime dependency is added for the ingress harness; it uses Node.js standard-library HTTP/HTTPS primitives and the OpenSSL binary available on the CI runner.

## Safety and rollback

This change is additive and opt-in. Rollback is to unset `DEVFORGE_PILOT_TRUST_INGRESS_CLIENT_IP` and stop using the production-like ingress suite. No database schema, migration history, authorization permission, production secret, payment configuration, or production deployment is changed.

## What this does not prove

This CI proof is not sufficient for production promotion by itself. The following remain deployment-specific gates:

- a real staging ingress/load balancer and certificate chain;
- network isolation proving the BFF/backend cannot be reached through an untrusted path that shares a trusted source CIDR;
- exact staging/production proxy CIDR ownership and change control;
- two truly distinct network clients behind the same deployed BFF producing distinct client rate-limit buckets;
- production secret delivery and rotation procedure;
- observability/alerting evidence in the deployed topology;
- deployment rollback rehearsal;
- generator-produced product proof and repeated product reuse.

Accordingly, this work strengthens production-like ingress evidence but does not promote `web-bff-core`, `web-session-core`, or `backend-core` beyond their current experimental status.
