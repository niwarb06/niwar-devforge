# Subscriptions Module

- Name: subscriptions
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral commerce contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers the catalog baseline for subscriptions only. Billing schedules, provider-specific behavior, payment execution, coupons/promotions, wallet/ledger behavior, and invoices/receipts are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`subscriptions-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `subscriptions-contract.json` — versioned subscriptions capability metadata.
- `validate_subscriptions_contract.py` — fail-closed repository validator.

Consumers may implement subscription lifecycle behavior in downstream applications, but product-specific billing rules must not be embedded in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- Product-specific identifiers, customer data, billing rules, and provider credentials must not be committed to this package.
- Subscription behavior must not bypass authorization or tenant boundaries in consuming applications.
- Payment execution and webhook verification belong outside this foundation contract.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_subscriptions_contract.py` proves:
- the committed contract is valid;
- the domain is `subscriptions`;
- the baseline capability is exactly `subscriptions`;
- missing, extra, reordered, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
