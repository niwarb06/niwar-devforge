# Booking Pack

- Name: booking
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the Phase-4 Booking/property product-pack composition contract defined by the DevForge roadmap and module catalog. This foundation slice covers only the catalog baseline: listings/properties, availability calendar, reservations, cancellation rules, and host/owner workflows.

The pack composes reusable capabilities for booking/property-family products. It does not implement product-specific entities, availability engines, reservation persistence, pricing, payments, cancellation execution, host dashboards, or UI behavior.

## Dependencies

None at runtime in this foundation slice. The repository validator and tests use only the Python standard library.

## Configuration

`booking-pack-contract.json` is the source of truth for this experimental composition contract.

## Public Interfaces

- `booking-pack-contract.json` — versioned Booking Pack capability metadata.
- `validate_booking_pack_contract.py` — fail-closed repository validator.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

No new permissions or RBAC rules are introduced. Host/owner authorization remains owned by shared identity/access modules and consuming applications.

## Security Considerations

- Product-specific schemas, customer data, property data, secrets, credentials, and tenant data must not be committed to this pack.
- Pack composition must not bypass authorization, tenant isolation, audit, privacy, or payment controls supplied by shared modules and consuming applications.
- No provider SDK or external runtime dependency is included in this foundation contract.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_booking_pack_contract.py` proves:
- the committed contract is valid;
- the pack is `booking`;
- baseline capabilities are exactly `listings_properties`, `availability_calendar`, `reservations`, `cancellation_rules`, then `host_owner_workflows`;
- missing, extra, reordered, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the pack name, baseline capability set/order, or schema version is a public composition-contract change and requires compatibility review for downstream packs, generators, and generated products.

The pack remains EXPERIMENTAL until runtime composition and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
