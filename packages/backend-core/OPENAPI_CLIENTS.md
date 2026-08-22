# OpenAPI Typed Client Workflow

DevForge treats the FastAPI OpenAPI schema as the transport-contract source of truth.

## Export

From `packages/backend-core`:

```bash
python scripts/export_openapi.py --output build/openapi.json
```

The exporter sorts JSON keys and writes a deterministic UTF-8 document suitable for CI artifacts and downstream client generators.

## Client generation

Generated web/mobile clients must be produced from the exported schema rather than handwritten duplicate request/response models.

Recommended adapters:

- Next.js/TypeScript: an approved OpenAPI TypeScript generator that emits typed request/response contracts and does not embed authentication secrets.
- Flutter/Dart: an approved OpenAPI Dart generator behind the DevForge API-client package boundary.

Generator choice and version must be pinned before generated code is promoted into a reusable module. Generated output must pass its platform lint/type/build checks and must not replace server-side authorization.

## Compatibility

API contract changes require review for backward compatibility. Breaking schema changes require a versioned API boundary or an explicit migration plan. CI validates that the backend can export a valid schema on every backend-core change.
