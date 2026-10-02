# Wallet Ledger Module

- Name: wallet_ledger
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral commerce contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers the catalog baseline for wallet/ledger only. Balance mutation rules, financial posting execution, provider-specific behavior, payment execution, subscriptions, coupons/promotions, and invoices/receipts are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`wallet-ledger-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `wallet-ledger-contract.json` — versioned wallet/ledger capability metadata.
- `validate_wallet_ledger_contract.py` — fail-closed repository validator.

Consumers may implement wallet and ledger behavior in downstream applications or adapters, but product-specific financial rules must not be embedded in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- Product-specific identifiers, customer financial data, balances, account details, and provider credentials must not be committed to this package.
- Wallet or ledger behavior must not bypass authorization or tenant boundaries in consuming applications.
- Real money movement, financial posting execution, persistence, reconciliation, and provider integration belong outside this foundation contract.
- No external ledger runtime dependency is included in this slice.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_wallet_ledger_contract.py` proves:
- the committed contract is valid;
- the domain is `wallet_ledger`;
- the baseline capability is exactly `wallet_ledger`;
- missing, extra, replaced, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
