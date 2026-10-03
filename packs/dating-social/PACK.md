# Dating/Social Pack

- Name: dating-social
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the Phase-4 Dating/Social product-pack composition contract defined by the DevForge roadmap and module catalog. This foundation slice covers only profiles, discovery, swipe/action model, match state, chat, privacy, and safety.

This slice defines composition metadata only. It does not implement product-specific profiles, discovery logic, action execution, matching algorithms, messaging runtime, privacy policy enforcement, moderation runtime, persistence, or UI behavior.

## Dependencies

None at runtime. The validator and tests use only the Python standard library.

## Configuration

`dating-social-pack-contract.json` is the source of truth for this experimental composition contract.

## Public Interfaces

- `dating-social-pack-contract.json`
- `validate_dating_social_pack_contract.py`

## Events / Webhooks

None.

## Data Models / Migrations

None.

## Permissions

No new permissions or RBAC rules are introduced.

## Security Considerations

- No product-specific profiles, private user data, secrets, credentials, or tenant data belong in this pack.
- Privacy and safety are composition requirements only in this foundation slice.
- No external provider runtime or SDK is included.
- Malformed or unsupported contract data fails validation.

## Tests

The tests verify the committed contract, pack name, exact ordered capability baseline, and rejection of missing, extra, reordered, or unknown fields.

## Upgrade Notes

Changing the pack name, baseline capability set/order, or schema version requires compatibility review.

The pack remains EXPERIMENTAL until runtime composition and generated-product use are separately approved and proven.
