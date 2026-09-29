# Search Module

- Name: search
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral discovery contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers the catalog baseline for search, filters, and pagination only. Favorites, reviews/ratings, recommendations, provider-specific search engines, and product-specific ranking behavior are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`search-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `search-contract.json` — versioned discovery capability metadata.
- `validate_search_contract.py` — fail-closed repository validator.

Consumers may implement these capabilities with local, database-backed, or external search mechanisms, but provider-specific behavior must not be embedded in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- Product-specific identifiers, domains, query data, ranking rules, and customer data must not be committed to this package.
- Search and filter behavior must not bypass authorization or tenant boundaries.
- Pagination inputs must be validated by consuming applications before use.
- External search-provider credentials or implementation details do not belong in this package.

## Tests

`tests/test_validate_search_contract.py` proves:
- the committed contract is valid;
- the domain is `search`;
- the baseline capabilities are exactly `search`, `filters`, and `pagination`;
- missing, reordered, extra, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
