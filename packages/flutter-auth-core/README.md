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
- Redirects are not followed by the default mobile transport.
- Response bodies are capped at 64 KiB by default.
- Raw session tokens are never included in `MobileLoginResult` or exception strings.
- Expired or backend-rejected (`401`) sessions are deleted from secure storage.
- Logout clears local storage only after the backend confirms `204` or `401`; transient failures retain the credential so server-side revocation can be retried.
- `clearLocalSession()` exists for an explicit local-only reset and is intentionally separate from secure logout.
- No password, session token, or response body is logged by this package.

## Secure storage adapter

The production adapter uses `flutter_secure_storage` `11.0.0`, pinned exactly in `pubspec.yaml`. The dependency is BSD-3-Clause and is isolated behind the `SecretStore` contract. Tests use an in-memory implementation so domain behavior remains provider-independent.

Version 11 requires Android API 23 or newer. Generated products must also follow the upstream platform setup guidance before release. See `THIRD_PARTY.md` for provenance and upgrade notes.

## DevForge backend contract proof

The proof currently covers these backend-core contracts:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/session`
- `DELETE /api/v1/auth/session`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me/profile`

FastAPI OpenAPI remains the source of truth. This package proves the mobile transport/session boundary; it is not yet the final generated Dart client pipeline.

## Development

CI pins Flutter `3.47.0` and runs formatting, analysis, and tests. The module remains EXPERIMENTAL until Android/iOS device integration, generated-client parity, broader failure-path coverage, and a production-like pilot are complete.
