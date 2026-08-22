# OpenAPI Typed Client Workflow

DevForge treats the FastAPI OpenAPI schema as the transport-contract source of truth.

## Export

From `packages/backend-core`:

```bash
python scripts/export_openapi.py --output build/openapi.json
```

The exporter sorts JSON keys and writes a deterministic UTF-8 document suitable for CI artifacts and downstream client generators.

## Current TypeScript proof

Backend Core CI currently performs an **experimental, generation-only proof** with `openapi-typescript` version `7.13.0`. The CLI consumes the exported schema and must produce TypeScript declarations containing the protected profile routes and `UserProfileResponse` contract.

Provenance for this CI-only tool:

- package: `openapi-typescript@7.13.0`
- upstream: `https://github.com/openapi-ts/openapi-typescript`
- license: MIT
- role: build-time schema-to-TypeScript declaration proof only
- no generated authentication secret, token, or runtime credential is committed

The version is explicitly pinned in CI. This proof does **not** yet promote a reusable TypeScript client package; a product/client package must add its own dependency lockfile, platform tests, and transport adapter before promotion.

## Current Flutter/Dart proof

`OpenAPI Dart Parity CI` performs a second experimental proof for the mobile contract:

- OpenAPI Generator CLI: `7.24.0`
- generator: `dart-dio` (stable generator)
- license: Apache-2.0
- configuration: `packages/flutter-auth-core/openapi-generator-config.json`
- parity verifier: `packages/flutter-auth-core/scripts/verify_openapi_parity.py`

The job exports the live FastAPI schema, generates an ephemeral Dart package, resolves/builds generated serializers, runs `dart analyze`, then verifies the mobile auth/profile route, status, bearer-security, schema, field-bound, and generated-source markers expected by `flutter-auth-core`.

Generated Dart output is intentionally temporary. It is **not** committed or approved as the mobile credential transport. The generated Dio/auth helpers must not replace the reviewed `DevForgeMobileAuthClient` TLS, no-redirect, secure-storage, revocation, and sanitized-error behavior without a separate compatibility/security review.

## Client generation

Generated web/mobile clients must be produced from the exported schema rather than handwritten duplicate request/response models.

Approved proof directions:

- Next.js/TypeScript: pinned `openapi-typescript` for declaration-generation proof; browser authentication remains server-mediated through the BFF/cookie boundary.
- Flutter/Dart: pinned OpenAPI Generator `dart-dio` for generation/parity proof; production adoption must sit behind the reviewed mobile credential/security boundary.

Generator choice and version must be pinned before generated code is promoted into a reusable module. Generated output must pass its platform lint/type/build checks and must not replace server-side authorization.

For web products, generated TypeScript code is a contract/client layer only. Browser JavaScript must not receive DevForge opaque bearer-session credentials; web authentication remains server-mediated through the BFF + Secure/HttpOnly cookie design. Mobile/API clients may use the documented bearer transport with credentials stored in platform secure storage.

## Compatibility

API contract changes require review for backward compatibility. Breaking schema changes require a versioned API boundary or an explicit migration plan. CI validates that the backend can export a valid schema on every backend-core change, while the Dart parity job checks that current mobile-auth assumptions and generated Dart output remain compatible with that schema.
