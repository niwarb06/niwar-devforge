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

See `THIRD_PARTY.md` for dependency provenance and upgrade findings.

## Configuration

- backend API base URL, normally ending in `/api/v1`
- request timeout, default 15 seconds
- optional explicit insecure localhost development exception
- injectable `AuthHttpTransport`
- injectable `SecretStore` through `SecureSessionVault`

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

## Tests and quality gates

CI must run:

- clean dependency resolution
- `dart format` verification
- `flutter analyze`
- `flutter test`
- dependency snapshot

CI setup actions are pinned to reviewed commit SHAs. Tests cover secure session persistence/expiry, token non-exposure in login results, refusal to replace an active session, best-effort revocation after secure-storage write failure, cleanup of valid-looking tokens from malformed successful responses, bearer translation, stale-401 cleanup, registration without implicit login, malformed login response rejection, secure logout retry semantics, TLS/local-development policy, secret-safe URL validation errors, bounded public error metadata, and sanitized exception strings.

## Current promotion blockers

- Android and iOS device/emulator integration tests against real platform secure storage
- OpenAPI-driven Dart client generation/parity proof instead of the current typed hand-written transport proof
- broader network/cancellation/background-resume failure paths
- dependency advisory/release automation for the Flutter package ecosystem
- at least one production-like pilot

## Upgrade notes

Changes to secure-storage keys, backend session response shape, TLS policy, login replacement policy, public error-code policy, logout semantics, or the storage provider require explicit compatibility/security review. `flutter_secure_storage` 11 removes deprecated pre-v10 algorithms; products with legacy secure-storage data must follow the upstream migration path before adopting v11 directly.
