# Notifications Module

- Name: notifications
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the provider-neutral notification contract defined by the DevForge Core Platform and module catalog. This first slice covers push-notification capability and preserves a strict provider-adapter boundary. Provider implementations, credentials, and product-specific delivery behavior are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`notifications-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `notifications-contract.json` — versioned notification capability metadata.
- `validate_notifications_contract.py` — fail-closed repository validator.

Consumers must treat the provider adapter as an external implementation boundary rather than embedding provider-specific behavior into reusable product logic.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice.

## Security Considerations

- Provider credentials and secrets must never be committed to this package.
- Product-specific identifiers, domains, and customer data must not be part of the reusable contract.
- Notification delivery must not alter authorization decisions.
- Provider-specific code belongs behind an adapter boundary.

## Tests

`tests/test_validate_notifications_contract.py` proves:
- the committed contract is valid;
- the domain is `notifications`;
- the baseline capability is `push_notifications`;
- a provider adapter is required;
- malformed or extra baseline capability values fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability, adapter requirement, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until a provider adapter and generated-product integration are separately approved, implemented, tested, and proven in a pilot or production-like environment.
