# Maps Module

- Name: maps
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the first provider-neutral Phase-3 maps/location contract for Niwar DevForge. This foundation slice establishes the `maps_adapter` capability and a strict provider boundary. Geocoding, current-location access, distance/radius search, live tracking, provider credentials, and product-specific location behavior are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`maps-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `maps-contract.json` — versioned maps/location capability metadata.
- `validate_maps_contract.py` — fail-closed repository validator.

Consumers must keep external map/provider behavior behind adapters rather than embedding provider-specific APIs or credentials into reusable product logic.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice. Access to user or device location requires a separately approved permission/consent design.

## Security Considerations

- Provider credentials and secrets must never be committed to this package.
- Coordinates, user location history, customer data, and product-specific identifiers do not belong in this reusable capability contract.
- Location capability must not bypass authentication, authorization, tenant isolation, or user consent requirements.
- Provider-specific code belongs behind an adapter boundary.

## Tests

`tests/test_validate_maps_contract.py` proves:
- the committed contract is valid;
- the domain is `maps`;
- the baseline capability is exactly `maps_adapter`;
- a provider adapter is required;
- extra or malformed baseline capability values fail validation;
- unknown contract keys fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability, adapter requirement, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until additional location capabilities, provider integration, generated-product integration, consent handling, and security tests are separately approved and proven.
