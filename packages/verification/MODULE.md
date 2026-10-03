# Verification Module

- Name: verification
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend

## Purpose

Provides the provider-neutral identity-verification capability contract defined by the DevForge Phase-3 roadmap and module catalog. This foundation slice covers only the `KYC/identity adapter` catalog baseline through the `kyc_identity_adapter` capability.

Verification provider integrations, identity-document handling, biometric/liveness processing, verification decisions, sanctions or watchlist screening, and product-specific onboarding behavior are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`verification-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `verification-contract.json` — versioned verification capability metadata.
- `validate_verification_contract.py` — fail-closed repository validator.

Consumers may implement identity-verification behavior behind separately reviewed adapters. Provider-specific services must not become authoritative in this reusable contract.

## Events / Webhooks

None in this foundation slice.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice. Consuming applications remain responsible for authorization and tenant boundaries before initiating or reading verification activity.

## Security Considerations

- Identity documents, biometric data, verification results, provider credentials, customer identifiers, and provider-specific metadata must not be committed to this package.
- Verification behavior must not bypass authorization, tenant isolation, consent, retention, or privacy requirements in consuming applications.
- No verification provider SDK or external KYC runtime dependency is approved by this foundation contract.
- Malformed or unsupported contract data fails validation.

## Tests

`tests/test_validate_verification_contract.py` proves:
- the committed contract is valid;
- the domain is `verification`;
- the baseline capability is exactly `kyc_identity_adapter`;
- missing, extra, replaced, or unknown contract fields fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability set/order, or schema version is a public-contract change and requires compatibility review for adapters, downstream modules, generators, and generated products.

The module remains EXPERIMENTAL until reviewed runtime integrations and generated-product use are separately approved, implemented, tested, and proven in a pilot or production-like environment.
