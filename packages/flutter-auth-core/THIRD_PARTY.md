# Third-Party Dependency Review

## flutter_secure_storage

- Package: `flutter_secure_storage`
- Approved version for this experimental proof: `11.0.0`
- Version pin: exact (`11.0.0`), not a floating caret range
- Upstream repository: `https://github.com/juliansteenbakker/flutter_secure_storage`
- Package registry: `https://pub.dev/packages/flutter_secure_storage`
- License: BSD-3-Clause
- Review date: 2026-08-22
- Decision: ADAPT through a provider interface; do not expose plugin types in DevForge auth domain contracts

### Reused surface

DevForge uses the public key/value secure-storage API through `FlutterSecureStorageSecretStore`. No upstream source code is copied into this repository.

### Security and compatibility findings

- the package provides platform-backed secure storage and is appropriate for storing opaque mobile session credentials
- version 11 uses newer Android cryptographic defaults and requires Android API 23+
- version 11 removed deprecated behavior from v10; existing apps with data written by pre-v10 deprecated algorithms should migrate through v10 before adopting v11
- the new DevForge module has no legacy secure-storage data, so that migration issue does not apply to the initial proof
- generated Android/iOS products must still verify upstream platform configuration and real-device behavior before release
- web support from the upstream package is not used by this module; DevForge browser authentication uses the separate BFF/cookie transport

### Attribution

The upstream BSD-3-Clause license and notices must be preserved where redistribution rules require them. This review records provenance; it is not a substitute for product release-license checks.

## subosito/flutter-action

- Use: CI-only Flutter SDK setup for `Flutter Auth Core CI`
- Upstream repository: `https://github.com/subosito/flutter-action`
- Pinned revision: `1a449444c387b1966244ae4d4f8c696479add0b2`
- License: MIT
- Review date: 2026-08-22
- Decision: APPROVED FOR EXPERIMENTAL CI USE at the pinned revision

The workflow does not track a floating `@v2` reference. The action is pinned to the reviewed commit so upstream tag movement cannot silently change the CI executable. No action source code is copied into the DevForge repository.
