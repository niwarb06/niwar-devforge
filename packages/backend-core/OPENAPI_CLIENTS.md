# OpenAPI Typed Client Workflow

DevForge treats the FastAPI OpenAPI schema as the transport-contract source of truth.

## Export

From `packages/backend-core`:

```bash
python scripts/export_openapi.py --output build/openapi.json
```

The exporter sorts JSON keys and writes a deterministic UTF-8 document suitable for CI artifacts and downstream client generators.

## Current TypeScript proof

Backend Core CI currently performs an **experimental, generation-only proof** with `openapi-typescript` version `7.13.0`. The CLI consumes the exported schema and must produce TypeScript declarations containing the credential, protected-profile, and logout routes plus their typed request/response contracts.

Provenance for this CI-only tool:

- package: `openapi-typescript@7.13.0`
- upstream: `https://github.com/openapi-ts/openapi-typescript`
- license: MIT
- role: build-time schema-to-TypeScript declaration proof only
- no generated authentication secret, token, or runtime credential is committed

The version is explicitly pinned in CI. This proof does **not** yet promote a reusable TypeScript client package; a product/client package must add its own dependency lockfile, platform tests, and transport adapter before promotion.

## Credential transport boundary

The schema includes:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `DELETE /api/v1/auth/session`
- protected profile routes

`POST /api/v1/auth/login` returns an opaque bearer session token for mobile/API/server-side transports. Browser JavaScript must not receive or persist this token. Web products call the credential API from their same-origin server/BFF and translate authenticated state into Secure + HttpOnly cookies according to `docs/16_AUTH_CORE_DECISION.md`.

Generated clients must preserve `Cache-Control: no-store` behavior around credential responses and must not add token logging.

## Client generation

Generated web/mobile clients must be produced from the exported schema rather than handwritten duplicate request/response models.

Recommended adapters:

- Next.js/TypeScript: an approved OpenAPI TypeScript generator that emits typed request/response contracts and does not embed authentication secrets.
- Flutter/Dart: an approved OpenAPI Dart generator behind the DevForge API-client package boundary.

Generator choice and version must be pinned before generated code is promoted into a reusable module. Generated output must pass its platform lint/type/build checks and must not replace server-side authorization.

For web products, generated TypeScript code is a contract/client layer only. Browser JavaScript must not receive DevForge opaque bearer-session credentials; web authentication remains server-mediated through the BFF + Secure/HttpOnly cookie design. Mobile/API clients may use the documented bearer transport with credentials stored in platform secure storage.

## Compatibility

API contract changes require review for backward compatibility. Breaking schema changes require a versioned API boundary or an explicit migration plan. CI validates that the backend can export a valid schema on every backend-core change.
