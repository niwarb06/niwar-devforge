# AI/SaaS Pack

- Name: ai_saas
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the Phase-4 AI/SaaS product-pack composition contract defined by the DevForge roadmap and module catalog. This foundation slice covers only workspaces, usage/metering, model/provider adapter, prompt/job history, and billing hooks.

This slice defines composition metadata only. It does not implement workspace persistence, usage metering runtime, model/provider execution, prompt/job storage or execution, billing processing, or UI behavior.

## Dependencies

None at runtime. The validator and tests use only the Python standard library.

## Configuration

`ai_saas-pack-contract.json` is the source of truth for this experimental composition contract.

## Public Interfaces

- `ai_saas-pack-contract.json`
- `validate_ai_saas_pack_contract.py`

## Events / Webhooks

None.

## Data Models / Migrations

None.

## Permissions

No new permissions or RBAC rules are introduced.

## Security Considerations

- No prompts, job histories, usage records, billing data, secrets, credentials, model inputs/outputs, or tenant data belong in this pack foundation.
- No external model, billing, or provider runtime or SDK is included.
- Malformed or unsupported contract data fails validation.

## Tests

The tests verify the committed contract, pack name, exact ordered capability baseline, and rejection of missing, extra, reordered, or unknown fields.

## Upgrade Notes

Changing the pack name, baseline capability set/order, or schema version requires compatibility review.

The pack remains EXPERIMENTAL until runtime composition and generated-product use are separately approved and proven.
