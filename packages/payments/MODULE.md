# Payments Module

- Name: payments
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral payments abstraction contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers the catalog baseline for a payments adapter only. Webhook processing, refunds, subscriptions, coupons/promotions, wallet/ledger, invoices/receipts, provider-specific behavior, and product-specific checkout logic are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`payments-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `payments-contract.json` — versioned payments-adapter capability metadata.
- `validate_payments_contract.py` — fail-closed repository validator.

Consumers may implement provider-specific payment behavior behind downstream adapters, but provider SDKs, credentials, money-movement logic, and product-specific checkout rules must not be embedded in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- No payment credentials, signing secrets, provider tokens, card data, bank data, or production endpoints belong in this package.
- This contract does not authorize, initiate, capture, refund, transfer, or settle funds.
- Consuming applications must enforce authorization, tenant boundaries, idempotency, webhook authenticity, auditability, and provider-specific compliance separately.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_payments_contract.py` proves:
- the committed contract is valid;
- the domain is `payments`;
- the baseline capability is exactly `payments_adapter`;
- missing, reordered, extra, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until provider integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
