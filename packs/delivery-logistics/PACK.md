# Delivery/Logistics Pack

- Name: delivery-logistics
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the Phase-4 Delivery/Logistics product-pack composition contract defined by the DevForge roadmap and module catalog. This foundation slice covers only orders, driver/courier state, assignment, route/location, and proof of delivery.

This slice defines composition metadata only. It does not implement order persistence, courier runtime state, assignment logic, routing/location tracking, proof capture, provider integrations, or UI behavior.

## Dependencies

None at runtime. The validator and tests use only the Python standard library.

## Configuration

`delivery-logistics-pack-contract.json` is the source of truth for this experimental composition contract.

## Public Interfaces

- `delivery-logistics-pack-contract.json`
- `validate_delivery_logistics_pack_contract.py`

## Events / Webhooks

None.

## Data Models / Migrations

None.

## Permissions

No new permissions or RBAC rules are introduced.

## Security Considerations

- No product-specific records, courier/customer data, secrets, credentials, or tenant data belong in this pack.
- No external routing, maps, courier, delivery, or proof provider runtime or SDK is included.
- Malformed or unsupported contract data fails validation.

## Tests

The tests verify the committed contract, pack name, exact ordered capability baseline, and rejection of missing, extra, reordered, or unknown fields.

## Upgrade Notes

Changing the pack name, baseline capability set/order, or schema version requires compatibility review.

The pack remains EXPERIMENTAL until runtime composition and generated-product use are separately approved and proven.
