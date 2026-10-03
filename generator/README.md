# Niwar DevForge Generator

Status: EXPERIMENTAL

The generator assembles product scaffolds from validated manifests and versioned DevForge templates. It is intentionally deterministic: the same generator version, template, manifest, and verified package bundle must produce byte-identical output.

## Current slice

The current generator supports two authentication blueprints:

- `web-next-auth`, composing `@niwar-devforge/web-bff-core` and `@niwar-devforge/web-session-core` into a Next.js product;
- `flutter-mobile-auth`, composing `flutter-auth-core` into a Flutter mobile product.

Both blueprints emit a deterministic `.devforge-generation.json` provenance record and a blueprint-specific `.github/workflows/ci.yml`. Web generated CI installs dependencies, typechecks, and builds with the existing generated npm contracts. Flutter generated CI resolves dependencies, verifies formatting, analyzes, and runs the generated test suite with the pinned Flutter contract. The generated workflows contain no deployment, release, staging, or production action.

Both blueprints also emit the source-backed local development files `infrastructure/dev/docker-compose.yml` and `infrastructure/dev/.env.example`. This generated dev setup contains only PostgreSQL 16 and Valkey 7.2.14 with the same health checks and local password placeholder as the committed DevForge development infrastructure. The Compose project name is derived from the validated product slug; no application container, deployment behavior, staging configuration, production configuration, or generated credential is included.

The standalone proof path can also vendor verified reusable package artifacts inside the generated repository so the product no longer depends on an adjacent DevForge checkout.

A manifest may now explicitly select one of the six Phase-4 product packs: `business`, `booking`, `marketplace`, `dating-social`, `delivery-logistics`, or `ai_saas`. The generator validates that selection against the committed pack contract and records the selected pack schema/capabilities in `.devforge-generation.json`. Pack selection has no default and does not yet compose pack runtime logic into the generated scaffold.

This still does not represent the complete Phase 5 generator. Admin/backend generation, database migrations, pack runtime composition, provider adapters, and broader application/service development-environment composition remain future work.

## Manifest contract

`schema_version` is currently `1`. Each blueprint requires its exact ordered module set. Product identifiers and package specifications are validated before output is written. The optional `pack` field is fail-closed against the six committed Phase-4 pack contracts; existing auth-only regression manifests may omit it.

Two dependency modes exist during migration:

1. `manifest-specs` — the earlier repository-local proof mode retained for regression compatibility.
2. `verified-vendored-bundle` — the standalone mode. Package artifacts are supplied through `--package-bundle`, SHA-256 verified, destination-confined to `vendor/`, and copied into the generated product.

New standalone product-repository proofs SHOULD use `verified-vendored-bundle`; they must not assume that `../../packages/...` exists outside the generated repository.

## Repository-local regression usage

```bash
node generator/generate.mjs \
  --manifest generator/manifests/web-auth-proof.json \
  --output .generated/generated-auth-proof
```

## Standalone package-bundle usage

First build the versioned package bundles after the reusable Web packages have been built:

```bash
node distribution/build-auth-bundle.mjs .package-bundle
```

Then generate a standalone Web product:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/web-auth-standalone-proof.json \
  --package-bundle .package-bundle/web \
  --output .generated/standalone-web
```

Or a standalone Flutter product:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/flutter-auth-standalone-proof.json \
  --package-bundle .package-bundle/flutter \
  --output .generated/standalone-flutter
```

The output directory must be absent or empty. The generator refuses to overwrite non-empty product directories.

## Package-bundle boundary

A package bundle contains a strict `bundle.json` descriptor and the referenced reusable artifacts. For every selected module the generator validates:

- the descriptor schema and exact module set;
- safe relative source and destination paths;
- a destination that exactly matches the generated dependency spec and lives under `vendor/`;
- file-vs-directory kind;
- SHA-256 integrity of the complete file or deterministic directory content.

All bundle validation and integrity checks happen before the output directory is written. A tampered artifact or destination mismatch therefore fails closed without leaving a partial generated product.

The current bundle builder emits:

- versioned npm tarballs for `web-bff-core` and `web-session-core`;
- a versioned relocatable package directory for `flutter-auth-core`.

No registry publication is performed by this proof path.

## Security and determinism

- unknown manifest/bundle keys fail closed;
- unsupported blueprint/module combinations fail closed;
- unsupported product-pack selections and malformed committed pack contracts fail closed;
- product identifiers are bounded and validated;
- template and bundle paths cannot escape their roots;
- package artifacts are integrity-checked before output writes;
- unknown/unresolved template tokens fail closed;
- output files use exclusive creation;
- generated CI workflow selection is fixed by the validated blueprint;
- generated local dev services and versions are fixed by the committed source-backed contract;
- the local database password remains an explicit placeholder rather than a generated credential;
- no timestamp or random identifier is written into generated output;
- no secrets, production domains, or credentials are generated.

## Proof gates

The legacy generator Web/Flutter CI continues to protect existing behavior. Generator tests additionally assert the generated local Docker/dev contract for both supported blueprints. `Standalone Package Distribution CI` additionally:

- runs generator and reusable-module tests;
- builds versioned package bundles;
- generates both standalone products twice and compares outputs byte-for-byte;
- proves no parent-monorepo package references exist;
- exports each generated product into `/tmp` and initializes it as a clean Git repository;
- deletes the source bundle and generated working directories before dependency installation;
- installs, audits, typechecks, and builds the Web product using Next.js default Turbopack;
- resolves, analyzes, and widget-tests the Flutter product using only its vendored reusable package.

Passing this gate proves that the generated auth products are relocatable outside the DevForge source checkout. It does not itself publish packages to a public/private registry, execute real staging, or authorize production.
