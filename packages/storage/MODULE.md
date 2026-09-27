# Storage Module

- Name: storage
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the provider-neutral storage capability contract for Niwar DevForge. This first slice covers the Core Platform storage/upload boundary already defined by the roadmap and module catalog: file upload, private access, signed access, and a provider-adapter boundary.

This package does not implement a storage provider and does not add image/video processing, product-specific media behavior, or UI integration.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`storage-contract.json` is the source of truth for the versioned baseline capability contract.

## Public Interfaces

- `storage-contract.json` — provider-neutral capability contract.
- `validate_storage_contract.py` — fail-closed validator for the committed contract.

Provider implementations must sit behind an adapter and must not make provider-specific identifiers authoritative in reusable product code.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

No authorization model is implemented here. Callers remain responsible for applying their existing authorization policy before granting upload or private/signed access.

## Security Considerations

- Private access remains the baseline for protected objects.
- Signed access must be treated as time-bounded delegated access by provider adapters; this contract does not mint URLs or credentials.
- Provider credentials, bucket/container identifiers, customer data, and product-specific paths must not be committed into this package.
- Storage capability selection must not bypass caller authorization.

## Tests

`tests/test_validate_storage_contract.py` proves:
- the committed contract is valid;
- all baseline capabilities are present;
- duplicate capabilities fail;
- malformed capability names fail;
- an unsupported schema version fails;
- a non-storage module identifier fails.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the contract schema version, module identifier, or baseline required capabilities is a public-contract change and requires compatibility review for adapters, generators, and generated products.

The module remains EXPERIMENTAL until at least one reviewed provider adapter and one generated/pilot integration prove the contract without leaking provider-specific behavior into reusable product code.
