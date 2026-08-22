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

- Use: CI-only Flutter SDK setup for `Flutter Auth Core CI` and OpenAPI Dart parity checks
- Upstream repository: `https://github.com/subosito/flutter-action`
- Pinned revision: `1a449444c387b1966244ae4d4f8c696479add0b2`
- License: MIT
- Review date: 2026-08-22
- Decision: APPROVED FOR EXPERIMENTAL CI USE at the pinned revision

The workflows do not track a floating `@v2` reference. The action is pinned to the reviewed commit so upstream tag movement cannot silently change the CI executable. No action source code is copied into the DevForge repository.

## OpenAPI Generator CLI / dart-dio

- Maven artifact: `org.openapitools:openapi-generator-cli`
- Approved version for this experimental proof: `7.24.0`
- Approved JAR SHA-256: `4b83ccc6fd43056c8c631cd0195e5100bd0550912502527bab09ac76152dab0c`
- Upstream repository: `https://github.com/OpenAPITools/openapi-generator`
- Distribution: Maven Central executable JAR over HTTPS
- Generator: `dart-dio`
- Generator status at review: STABLE
- License: Apache-2.0
- Review date: 2026-08-22
- Decision: APPROVED FOR EPHEMERAL CONTRACT GENERATION/PARITY CI ONLY

### Why this generator

The `dart-dio` generator is the OpenAPI Generator Dart client option with bearer-token support and support for composite/union OpenAPI schemas. That makes it a better contract-generation proof for FastAPI OpenAPI 3.x than copying request/response models by hand.

### Reused surface

DevForge invokes the published CLI JAR with the committed `openapi-generator-config.json`. The generator consumes the deterministic backend OpenAPI document and writes a temporary Dart package in CI. No OpenAPI Generator source code is copied into this repository. CI verifies both the exact JAR SHA-256 and the reported CLI version before executing generation.

### Security and compatibility findings

- OpenAPI Generator `7.24.0` currently reports its OpenAPI 3.1 support as beta; the current FastAPI schema therefore remains a generation/parity proof that must be revalidated on generator or schema upgrades
- the current backend OpenAPI document does not declare a `servers` entry, so generated `dart-dio` output falls back to `http://localhost`; this is another reason the generated transport must not be used directly for production credentials
- the proof uses the stable `built_value` serialization path; optional/patch-only generator modes were deliberately not enabled because that combination produced invalid generated BuiltValue code for the nullable profile PATCH field in this version
- the backend currently treats omitted and explicit-null `display_name` as the same value, so the parity proof does not require generated absent-vs-null PATCH semantics
- raw `dart-dio` output currently emits a small set of generator-origin analyzer warnings such as unused imports; CI reports those warnings but fails on analyzer errors, while handwritten `flutter-auth-core` keeps its stricter warning-free analysis gate

### Security and adoption limits

- generated code is not committed, published, or used as the authoritative mobile credential transport in this proof
- the generated Dio/auth layer is not approved to replace `DevForgeMobileAuthClient` security behavior without a separate transport/security review
- generated runtime dependencies such as Dio/built-value tooling are transient CI proof dependencies here; this review does not automatically approve them for a shipped product
- mobile opaque session credentials must continue to use reviewed platform secure storage and the DevForge revocation/TLS/error-handling rules
- generator version, generator type, serialization strategy, or generated-runtime adoption requires compatibility/security review
- CI fails if checksum/version verification, generation, serializer build, analyzer errors, or contract parity fails; generator-origin warnings remain visible in logs for review

### Attribution

OpenAPI Generator is Apache-2.0 licensed. If generated artifacts or generator-derived notices are later redistributed, release packaging must preserve any notices/attribution required by the generator and by generated runtime dependencies. This proof keeps generated output ephemeral.
