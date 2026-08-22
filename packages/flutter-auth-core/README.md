# Flutter Auth Core

Reusable Android/iOS authentication transport proof for Niwar DevForge.

The package keeps the backend opaque session credential in platform secure storage and exposes typed registration, login, current-profile, profile-update, and logout flows without returning the raw session token from `login()`.

## Basic setup

```dart
import 'package:flutter/widgets.dart';
import 'package:niwar_devforge_flutter_auth/niwar_devforge_flutter_auth.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final vault = SecureSessionVault(
    FlutterSecureStorageSecretStore(),
  );
  final auth = DevForgeMobileAuthClient(
    backendApiBaseUrl: Uri.parse('https://api.example.com/api/v1'),
    sessionVault: vault,
  );

  runApp(const MyApp());
}
```

`login()` stores the opaque backend session in the vault and returns only authentication state plus expiry metadata. Protected requests read the token from the vault and add `Authorization: Bearer ...` inside the transport boundary.

## Security defaults

- HTTPS is required for normal backend URLs.
- Plain HTTP is accepted only for `localhost`, `127.0.0.1`, or `::1` when `allowInsecureLocalhostForDevelopment: true` is explicitly set.
- Invalid base-URL errors do not echo the supplied URI, so accidentally embedded credentials/query secrets are not reflected into exception text.
- Redirects are not followed by the default mobile transport.
- Response bodies are capped at 64 KiB by default.
- Raw session tokens are never included in `MobileLoginResult` or exception strings.
- Expired or backend-rejected (`401`) sessions are deleted from secure storage.
- A second login is rejected while a valid local session already exists; callers must explicitly logout first instead of silently replacing a credential and orphaning the older server session.
- If the backend creates a new session but secure persistence fails, the client immediately attempts server-side revocation of that unpersisted token and returns a sanitized storage error.
- If a `200` login response contains a valid-looking token but malformed companion session metadata, the client attempts immediate server-side revocation before rejecting the response.
- Public API error codes are accepted only when they match the bounded canonical DevForge code shape; unsafe values fall back to `request_failed`.
- `Retry-After` metadata is exposed only when it is a positive bounded integer.
- Logout clears local storage only after the backend confirms `204` or `401`; transient failures retain the credential so server-side revocation can be retried.
- `clearLocalSession()` exists for an explicit local-only reset and is intentionally separate from secure logout.
- Secure-storage read/write/clear failures exposed by the client use sanitized error codes rather than raw provider exceptions.
- No password, session token, raw response body, or supplied secret-bearing base URL is logged by this package.

## Secure storage adapter

The production adapter uses `flutter_secure_storage` `11.0.0`, pinned exactly in `pubspec.yaml`. The dependency is BSD-3-Clause and is isolated behind the `SecretStore` contract. Tests use an in-memory implementation so domain behavior remains provider-independent.

Version 11 requires Android API 23 or newer. Generated products must also follow the upstream platform setup guidance before release. See `THIRD_PARTY.md` for provenance and upgrade notes.

## DevForge backend contract proof

The proof covers these backend-core contracts:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/session`
- `DELETE /api/v1/auth/session`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me/profile`

FastAPI OpenAPI remains the source of truth. In addition to the hand-written secure transport proof, CI now exports the live backend schema, generates an ephemeral Dart client with OpenAPI Generator `7.24.0` using the stable `dart-dio` generator, builds the generated serializers, analyzes the generated package, and runs `scripts/verify_openapi_parity.py`.

The parity verifier locks the mobile-auth assumptions that matter most: endpoint/method/status pairs, `DevForgeSession` bearer security, request/response component names, credential field bounds, session response invariants, profile shape, and presence of the same routes/models in generated Dart source.

The generated package is **not committed, published, or used as the mobile credential transport yet**. Its generated Dio/auth layer must not bypass this module's HTTPS, no-redirect, secure-storage, revocation, and sanitized-error policies. A later integration step can reuse generated contract models/API signatures behind the reviewed mobile security boundary.

Generator options are recorded in `openapi-generator-config.json`; provenance and adoption limits are in `THIRD_PARTY.md`.

## Development

`Flutter Auth Core CI` pins Flutter `3.47.0` and runs formatting, analysis, tests, and a dependency snapshot. `OpenAPI Dart Parity CI` additionally exports backend OpenAPI, generates/builds/analyzes the ephemeral Dart client, and runs the parity verifier. The module remains EXPERIMENTAL until Android/iOS device integration, reviewed generated-client runtime integration, broader failure-path coverage, and a production-like pilot are complete.
