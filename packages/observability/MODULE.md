# Observability Module

- Name: observability
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: backend, web, admin, mobile, worker

## Purpose

Defines the provider-neutral observability contract for the Core Platform. This first slice standardizes structured logging and request correlation only, matching capabilities already present in `backend-core` and the Phase 2 roadmap without adding a second runtime implementation.

## Dependencies

None at runtime. Validation and tests use only the Python standard library.

## Configuration

`observability-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `observability-contract.json` — versioned provider-neutral capability contract.
- `validate_observability_contract.py` — fail-closed repository validator.

The baseline capabilities are:
- `structured_logging`
- `request_correlation`

The baseline correlation field is `request_id`.

## Events / Webhooks

None.

## Data Models / Migrations

None.

## Permissions

None. Observability data must never become an authorization source.

## Security Considerations

- Secrets, credentials, session tokens, and sensitive personal data must not be required by this contract.
- Correlation identifiers are diagnostic metadata, not authentication or authorization credentials.
- Provider/exporter configuration belongs outside this package.
- This slice does not add metrics, tracing, telemetry exporters, or external monitoring providers.

## Tests

`tests/test_validate_observability_contract.py` proves:
- the committed contract is valid;
- required baseline capabilities are present;
- duplicate capabilities fail;
- unknown capabilities fail in this V1 slice;
- `request_id` remains the required correlation field;
- external exporter requirements remain disabled in this provider-neutral foundation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Adding metrics, tracing, exporters, provider-specific fields, or changing the correlation contract is a public-contract expansion and requires an explicit future scope decision. The module remains EXPERIMENTAL until it is integrated across generated products and proven through broader cross-runtime tests.
