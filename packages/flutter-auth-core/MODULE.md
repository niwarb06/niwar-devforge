# Flutter Auth Core Module

- Name: flutter-auth-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Supported targets: Flutter Android/iOS mobile clients

## Purpose

Provides a reusable, typed mobile authentication boundary for DevForge products while keeping opaque backend session credentials in platform secure storage.

## Dependencies

- Flutter SDK; CI proof pinned to Flutter `3.47.0`
- `flutter_secure_storage` `11.0.0`, BSD-3-Clause, isolated behind `SecretStore`
- Dart `dart:io` for the default Android/iOS HTTP transport
- OpenAPI Generator CLI `7.24.0`, Apache-2.0, build-time parity proof only; generated output is ephemeral and not a runtime dependency of this module

See `THIRD_PARTY.md` for dependency provenance and upgrade findings.

## Configuration

- backend API base URL, normally ending in `/api/v1`
- request timeout, default 15 seconds
- optional explicit insecure localhost development exception
- injectable `AuthHttpTransport`
- injectable `SecretStore` through `SecureSessionVault`
- OpenAPI generation options in `openapi-generator-config.json`

## Public interfaces

- `DevForgeMobileAuthClient`
- `AuthHttpTransport` / `IoAuthHttpTransport`
- `AuthHttpResponse`
- `SecretStore`
- `FlutterSecureStorageSecretStore`
- `SecureSessionVault`
- `StoredSession`
- `UserProfile`
- `MobileLoginResult`
- `LogoutResult`
- typed sanitized exception classes

Generated Dart code is not a public runtime interface of this module yet.

## Transport contract

- `register()` -> `POST /auth/register`
- `login()` -> `POST /auth/session`
- `logout()` -> `DELETE /auth/session`
- `currentProfile()` -> `GET /users/me`
- `updateProfile()` -> `PATCH /users/me/profile`

The configured base URL supplies the backend API prefix. FastAPI OpenAPI remains the authoritative transport schema.

## Security considerations

- production/non-local URLs require HTTPS
- invalid base-URL validation errors never echo the supplied URI, avoiding accidental credential/query-secret reflection
- the default transport refuses redirects
- response bodies are size bounded
- login response session tokens are persisted to secure storage before login completes and are not returned to application UI state
- a valid existing local session blocks another login so the previous server session is not silently orphaned
- if secure persistence of a newly created backend session fails, the client immediately attempts server-side revocation of the unpersisted token and returns a sanitized storage error
- if a successful login contains a valid-looking token but malformed companion metadata, the client attempts immediate revocation before rejecting the response
- public backend error codes must match the bounded canonical lowercase/underscore code shape or the client uses `request_failed`
- `Retry-After` is exposed only when it is a positive integer of at most 86,400 seconds
- secure-storage provider read/write/clear failures exposed through the client are mapped to sanitized error codes
- secure storage records include explicit expiry; malformed/expired records are deleted
- `401` on protected requests clears stale local session state
- logout keeps the secure token when server revocation cannot be confirmed, enabling a retry instead of silently orphaning a still-active server session
- `clearLocalSession()` is an explicit local-only escape hatch and must not be presented as equivalent to server logout
- no package logging of passwords, bearer tokens, raw response bodies, or supplied secret-bearing base URLs
- Android/iOS platform setup for `flutter_secure_storage` must be verified in generated applications
- this module is not a web auth transport; browser products use `web-bff-core`
- generated `dart-dio` transport/auth helpers are contract evidence only and are not approved to replace the reviewed mobile credential boundary without a separate security/integration review

## OpenAPI-generated Dart parity proof

`OpenAPI Dart Parity CI` performs a generation-only compatibility gate:

1. installs backend-core and exports the deterministic FastAPI OpenAPI schema;
2. runs OpenAPI Generator CLI `7.24.0` with the stable `dart-dio` generator and `openapi-generator-config.json`;
3. resolves generated dependencies and builds generated serializers;
4. runs `dart analyze` against the generated package;
5. runs `scripts/verify_openapi_parity.py` against both the exported schema and generated Dart output.

The verifier covers the five mobile auth/profile routes, expected success status codes, `DevForgeSession` bearer protection on authenticated operations, request/response schema references, credential length constraints, session metadata invariants, profile shape, and generated-source route/model markers.

Generated output is placed in a temporary CI directory. It is not committed, distributed, or granted authority over secure session storage.

## Tests and quality gates

CI must run:

- clean Flutter dependency resolution
- `dart format` verification
- `flutter analyze`
- `flutter test`
- Flutter dependency snapshot
- deterministic backend OpenAPI export for parity jobs
- pinned OpenAPI Dart generation proof
- generated Dart serializer build
- generated Dart analysis
- OpenAPI/generated-source parity verification

CI setup actions used by the Flutter module are pinned to reviewed commit SHAs. Tests cover secure session persistence/expiry, token non-exposure in login results, refusal to replace an active session, best-effort revocation after secure-storage write failure, cleanup of valid-looking tokens from malformed successful responses, bearer translation, stale-401 cleanup, registration without implicit login, malformed login response rejection, secure logout retry semantics, TLS/local-development policy, secret-safe URL validation errors, bounded public error metadata, and sanitized exception strings.

## Current promotion blockers

- Android and iOS device/emulator integration tests against real platform secure storage
- reviewed integration of generated API contracts/signatures behind the existing secure mobile transport boundary
- broader network/cancellation/background-resume failure paths
- dependency advisory/release automation for the Flutter package ecosystem
- at least one production-like pilot

## Upgrade notes

Changes to secure-storage keys, backend session response shape, TLS policy, login replacement policy, public error-code policy, logout semantics, the storage provider, OpenAPI Generator version, generator type, or generated-runtime adoption require explicit compatibility/security review. `flutter_secure_storage` 11 removes deprecated pre-v10 algorithms; products with legacy secure-storage data must follow the upstream migration path before adopting v11 directly.
