# Reviews Module

- Name: reviews
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral discovery contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers the catalog baseline for reviews and ratings only. Moderation workflows, comments, reactions, recommendations, provider-specific behavior, and product-specific ranking logic are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`reviews-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `reviews-contract.json` — versioned reviews/ratings capability metadata.
- `validate_reviews_contract.py` — fail-closed repository validator.

Consumers may implement review and rating persistence in downstream applications, but product-specific behavior must not be embedded in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- Product-specific identifiers, customer data, moderation policy, and ranking rules must not be committed to this package.
- Reviews and ratings must not bypass authorization or tenant boundaries in consuming applications.
- Provider credentials or implementation details do not belong in this package.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_reviews_contract.py` proves:
- the committed contract is valid;
- the domain is `reviews`;
- the baseline capabilities are exactly `reviews` and `ratings`;
- missing, reordered, extra, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
