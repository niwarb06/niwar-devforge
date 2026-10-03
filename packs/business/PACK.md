# Business Pack

- Name: business
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the Phase-4 Business/CRUD product-pack composition contract defined by the DevForge roadmap and module catalog. This foundation slice covers only the catalog baseline: CRUD, dashboards, reports, roles, and export/import.

The pack composes reusable capabilities for business-family products. It does not implement product-specific entities, workflows, persistence, permissions, reporting engines, import/export runtimes, or UI behavior.

## Dependencies

None at runtime in this foundation slice. The repository validator and tests use only the Python standard library.

## Configuration

`business-pack-contract.json` is the source of truth for this experimental composition contract.

## Public Interfaces

- `business-pack-contract.json` — versioned Business Pack capability metadata.
- `validate_business_pack_contract.py` — fail-closed repository validator.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

No new permissions or RBAC rules are introduced. The `roles` capability is a composition requirement from the catalog; authorization remains owned by the shared identity/access modules and consuming applications.

## Security Considerations

- Product-specific schemas, customer data, secrets, business identifiers, credentials, and tenant data must not be committed to this pack.
- Pack composition must not bypass authorization, tenant isolation, audit, or data-protection controls supplied by shared modules and consuming applications.
- No provider SDK or external runtime dependency is included in this foundation contract.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_business_pack_contract.py` proves:
- the committed contract is valid;
- the pack is `business`;
- baseline capabilities are exactly `crud`, `dashboards`, `reports`, `roles`, then `export_import`;
- missing, extra, reordered, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the pack name, baseline capability set/order, or schema version is a public composition-contract change and requires compatibility review for downstream packs, generators, and generated products.

The pack remains EXPERIMENTAL until runtime composition and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
