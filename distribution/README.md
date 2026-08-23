# DevForge Package Distribution

Status: EXPERIMENTAL

This directory contains the repository-side packaging proof used to export reusable DevForge modules into generated standalone product repositories without requiring an adjacent DevForge monorepo checkout.

## Current distribution format

`build-auth-bundle.mjs` creates two platform-specific bundles:

- `web/` contains versioned npm tarballs for `@niwar-devforge/web-bff-core` and `@niwar-devforge/web-session-core`;
- `flutter/` contains a relocatable versioned directory for `niwar_devforge_flutter_auth`.

Package versions are read from the source package metadata. The builder does not publish to npm, pub.dev, GHCR, or another registry.

Each bundle contains a strict `bundle.json` descriptor. Every module entry records:

- `kind`: `file` or `directory`;
- `source`: a safe relative path inside the bundle;
- `destination`: the exact `vendor/` location expected by the generated product manifest;
- `sha256`: the integrity digest of the complete artifact or deterministic directory contents.

## Generator trust boundary

When `generator/generate.mjs` receives `--package-bundle`, it validates the complete bundle before writing the output product. The generator:

1. rejects unknown descriptor/module keys;
2. requires the exact module set selected by the blueprint;
3. rejects absolute paths, traversal segments, backslash paths, and symbolic-link sources;
4. realpath-confines bundle sources to the bundle root;
5. verifies SHA-256 before output creation;
6. requires the destination to exactly match the generated dependency spec and remain under `vendor/`;
7. verifies the copied artifact again after copy;
8. records the verified digest and `verified-vendored-bundle` dependency mode in `.devforge-generation.json`.

A validation or integrity failure is fail-closed and does not create a partial product output directory.

## Standalone Web behavior

The standalone Web proof uses vendored npm tarballs referenced by `file:./vendor/...`. Because dependencies now live inside the generated repository, its generated `npm run build` uses the normal `next build` command and therefore Next.js default Turbopack. The legacy repository-local proof keeps `next build --webpack` for compatibility with its external monorepo-relative `file:` dependencies.

## Standalone Flutter behavior

The standalone Flutter proof uses a generated-repository-local path under `vendor/`. `flutter pub get`, static analysis, and widget tests therefore resolve the reusable auth package without a parent DevForge checkout.

## Proof boundary

`Standalone Package Distribution CI` exports the generated Web and Flutter products into clean temporary Git repositories, removes the source bundle/working generation directories, and then installs/builds/tests from those standalone repositories.

This proves relocatability and package integrity for the current auth slice. It does **not** publish packages to a registry, create production releases, deploy staging/production, or authorize a merge.
