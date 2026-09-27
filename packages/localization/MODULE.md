# Localization Module

- Name: localization
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the platform-neutral locale contract for Niwar DevForge products. The initial baseline is Kurdish (`ku`), Arabic (`ar`), and English (`en`) with explicit RTL/LTR direction metadata. Product-specific translations are intentionally not stored in this core package.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`locales.json` is the source of truth. It defines the default locale and supported locale metadata.

## Public Interfaces

- `locales.json` — versioned locale metadata contract.
- `validate_locales.py` — fail-closed repository validator for the contract.

Consumers must use locale metadata instead of inferring text direction from UI strings.

## Events / Webhooks

None.

## Data Models / Migrations

None.

## Permissions

None.

## Security Considerations

- Locale selection must never authorize data access or change permission checks.
- Unsupported or malformed locale metadata fails validation rather than silently changing direction behavior.
- No secrets, product identifiers, customer data, or provider-specific configuration belong in this package.

## Tests

`tests/test_validate_locales.py` proves:
- the committed contract is valid;
- `ku` and `ar` are RTL;
- `en` is LTR;
- duplicate locale codes fail;
- missing required baseline locales fail;
- invalid direction values fail;
- the default locale must be supported.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing a locale code, default locale, direction, or contract schema version is a public-contract change and requires compatibility review for generated products and UI shells.

The module remains EXPERIMENTAL until it is integrated into generated Web, Admin, and Flutter products and proven through bidi/i18n tests in at least one pilot or production-like environment.
