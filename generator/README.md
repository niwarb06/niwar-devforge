# Niwar DevForge Generator

Status: EXPERIMENTAL

The generator assembles product scaffolds from validated manifests and versioned DevForge templates. It is intentionally deterministic: the same generator version, template, manifest, and verified package bundle must produce byte-identical output.

## Current slice

The current generator supports two authentication blueprints:

- `web-next-auth`, composing `@niwar-devforge/web-bff-core` and `@niwar-devforge/web-session-core` into a Next.js product;
- `flutter-mobile-auth`, composing `flutter-auth-core` into a Flutter mobile product.

Both blueprints emit a deterministic `.devforge-generation.json` provenance record. The standalone proof path can also vendor verified reusable package artifacts inside the generated repository so the product no longer depends on an adjacent DevForge checkout.

This still does not represent the complete Phase 5 generator. Admin/backend generation, database migrations, product packs, provider adapters, and generated CI/dev-environment breadth remain future work.

## Manifest contract

`schema_version` is currently `1`. Each blueprint requires its exact ordered module set. Product identifiers and package specifications are validated before output is written.

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
- product identifiers are bounded and validated;
- template and bundle paths cannot escape their roots;
- package artifacts are integrity-checked before output writes;
- unknown/unresolved template tokens fail closed;
- output files use exclusive creation;
- no timestamp or random identifier is written into generated output;
- no secrets, production domains, or credentials are generated.

## Proof gates

The legacy generator Web/Flutter CI continues to protect existing behavior. `Standalone Package Distribution CI` additionally:

- runs generator and reusable-module tests;
- builds versioned package bundles;
- generates both standalone products twice and compares outputs byte-for-byte;
- proves no parent-monorepo package references exist;
- exports each generated product into `/tmp` and initializes it as a clean Git repository;
- deletes the source bundle and generated working directories before dependency installation;
- installs, audits, typechecks, and builds the Web product using Next.js default Turbopack;
- resolves, analyzes, and widget-tests the Flutter product using only its vendored reusable package.

Passing this gate proves that the generated auth products are relocatable outside the DevForge source checkout. It does not itself publish packages to a public/private registry, execute real staging, or authorize production.
