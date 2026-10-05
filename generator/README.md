# Niwar DevForge Generator

Status: EXPERIMENTAL

The generator assembles product scaffolds from validated manifests and versioned DevForge templates. It is intentionally deterministic: the same generator version, template, manifest, and verified package bundle must produce byte-identical output.

## Current slice

The current generator supports three authentication-oriented blueprints:

- `web-next-auth`, composing `@niwar-devforge/web-bff-core` and `@niwar-devforge/web-session-core` into a Next.js product;
- `flutter-mobile-auth`, composing `flutter-auth-core` into a Flutter mobile product;
- `backend-fastapi-auth`, composing the existing `backend-core` into a thin runnable FastAPI backend scaffold.

The Phase-5 Admin scaffold foundation intentionally reuses the existing `web-next-auth` blueprint because the canonical architecture defines both Web and Admin on Next.js + TypeScript. `generator/manifests/admin-auth-proof.json` gives that generated surface an explicit Admin product identity without duplicating the authentication template or inventing Admin business UI or authorization policy.

All three blueprints emit a deterministic `.devforge-generation.json` provenance record and a blueprint-specific `.github/workflows/ci.yml`. Web generated CI installs dependencies, typechecks, and builds with the existing generated npm contracts. Flutter generated CI resolves dependencies, verifies formatting, analyzes, and runs the generated test suite with the pinned Flutter contract. Backend generated CI installs the selected backend-core path, executes the generated Python `unittest` skeleton, and imports the FastAPI application. The generated workflows contain no deployment, release, staging, or production action.

The Web blueprint also emits a dependency-free `node:test` scaffold at `test/scaffold.test.mjs`, an `npm test` script, and `.github/workflows/test.yml` to run that skeleton on push and pull requests. The test workflow uses the same pinned Node/checkout baseline and contains no deployment, release, staging, production, provider, or secret-consuming behavior.

The backend blueprint emits `.env.example`, `requirements.txt`, `app.py`, and `tests/test_scaffold.py`. Repository-local proofs may select `../../packages/backend-core`; standalone generation may instead select the verified versioned backend-core source directory vendored under `vendor/`. Backend output also carries the canonical backend-core `alembic.ini`, `migrations/env.py`, and `migrations/script.py.mako` runner/config files and documents the explicit operator-run migration command; generation itself never executes migrations.

All current blueprints also emit the source-backed local development files `infrastructure/dev/docker-compose.yml` and `infrastructure/dev/.env.example`. This generated dev setup contains only PostgreSQL 16 and Valkey 7.2.14 with the same health checks and local password placeholder as the committed DevForge development infrastructure. The Compose project name is derived from the validated product slug; no application container, deployment behavior, staging configuration, production configuration, or generated credential is included.

All current blueprints also emit the canonical backend-core Alembic revision history at `migrations/versions/`. The generator carries source-backed snapshots of committed revisions `0001_backend_core_baseline` through `0003_roles_tenants` inside its own assets so generation remains self-contained; regression tests require those snapshots and emitted files to stay byte-identical to the canonical backend-core revisions. It does not invent or modify migration history. The Backend blueprint additionally emits the canonical backend-core Alembic runner/config files, regression-checked byte-for-byte against their source; Web, Flutter, and Admin outputs do not receive backend-only runner wiring. Generation does not execute database migrations.

The standalone proof path can vendor verified reusable package artifacts inside the generated repository so the Web, Flutter, and Backend products no longer depend on an adjacent DevForge checkout.

A manifest may explicitly select one of the six Phase-4 product packs: `business`, `booking`, `marketplace`, `dating-social`, `delivery-logistics`, or `ai_saas`. The generator validates that selection against the committed pack contract and records the selected pack schema/capabilities in `.devforge-generation.json`. Pack selection has no default and does not yet compose pack runtime logic into the generated scaffold.

This still does not represent the complete Phase 5 generator. Admin-specific UI/authorization composition, pack runtime composition, provider adapters, and broader application/service development-environment composition remain future work.

## Manifest contract

`schema_version` is currently `1`. Each blueprint requires its exact ordered module set. Product identifiers and package specifications are validated before output is written. The optional `pack` field is fail-closed against the six committed Phase-4 pack contracts; existing auth-only regression manifests may omit it.

Two dependency modes exist during migration:

1. `manifest-specs` — the repository-local proof mode retained for regression compatibility.
2. `verified-vendored-bundle` — the standalone mode. Package artifacts are supplied through `--package-bundle`, SHA-256 verified, destination-confined to `vendor/`, and copied into the generated product.

New standalone product-repository proofs SHOULD use `verified-vendored-bundle`; they must not assume that `../../packages/...` exists outside the generated repository. The current bundle builder covers Web, Flutter, and Backend authentication foundations.

## Repository-local regression usage

```bash
node generator/generate.mjs \
  --manifest generator/manifests/web-auth-proof.json \
  --output .generated/generated-auth-proof
```

Generate the Admin scaffold proof with:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/admin-auth-proof.json \
  --output .generated/generated-admin-proof
```

Generate the backend scaffold proof with:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/backend-auth-proof.json \
  --output .generated/generated-backend-proof
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

Or a standalone Backend product:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/backend-auth-standalone-proof.json \
  --package-bundle .package-bundle/backend \
  --output .generated/standalone-backend
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
- a versioned relocatable package directory for `flutter-auth-core`;
- a versioned relocatable Python source package directory for `backend-core`.

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
- the generated Web test skeleton uses only Node built-ins and its workflow is test-only;
- the generated backend scaffold reuses the canonical backend-core application rather than reimplementing backend auth/domain behavior;
- generated local dev services and versions are fixed by the committed source-backed contract;
- generated database migration assets are regression-checked byte-for-byte against the committed backend-core revision sources;
- generated Backend Alembic runner/config files are regression-checked byte-for-byte against the committed backend-core sources;
- the local database password remains an explicit placeholder rather than a generated credential;
- no timestamp or random identifier is written into generated output;
- no secrets, production domains, or credentials are generated.

## Proof gates

The existing generator Web/Flutter CI continues to protect existing behavior. `Generator Backend Auth CI` additionally runs the complete generator regression suite, generates the backend scaffold, installs the repository-local backend-core dependency, executes the generated Python test skeleton, and imports the generated FastAPI application. `Generator Admin Auth CI` generates the Admin proof twice, proves byte-identical output, then installs, tests, typechecks, and builds the generated Admin product against the existing reusable Web authentication modules. Generator tests also execute the generated Web test skeleton, assert generated local Docker/dev contracts, verify byte-identical canonical database migrations and Backend Alembic runner/config files, and prove deterministic backend and Admin scaffold output.

`Standalone Package Distribution CI` additionally:

- runs generator and reusable-module tests;
- builds versioned Web, Flutter, and Backend package bundles;
- generates all three standalone products twice and compares outputs byte-for-byte;
- proves no parent-monorepo package references exist;
- exports each generated product into `/tmp` and initializes it as a clean Git repository;
- deletes the source bundle and generated working directories before dependency installation;
- installs, audits, typechecks, and builds the Web product using Next.js default Turbopack;
- resolves, analyzes, and widget-tests the Flutter product using only its vendored reusable package;
- installs the Backend product from its vendored backend-core source package, runs the generated unittest skeleton, and imports the FastAPI application.

Passing the standalone gate proves that the generated Web, Flutter, and Backend auth products are relocatable outside the DevForge source checkout. It does not publish packages to a public/private registry, execute real staging, or authorize production.
