# Niwar DevForge Generator

Status: EXPERIMENTAL

The generator assembles product scaffolds from validated manifests and versioned DevForge templates. It is intentionally deterministic: the same generator version, template, and manifest must produce byte-identical output.

## Current slice

The first blueprint is `web-next-auth`. It emits a minimal Next.js product scaffold that composes:

- `@niwar-devforge/web-bff-core` for the server-side browser credential boundary;
- `@niwar-devforge/web-session-core` for browser session revalidation;
- login, logout, registration, and current-session route handlers;
- a minimal browser auth UI;
- strict TypeScript and production build configuration;
- safe environment examples and a deterministic `.devforge-generation.json` provenance record.

This slice does not yet represent the complete Phase 5 generator. Mobile/admin/backend generation, database migrations, product packs, provider adapters, generated CI workflows, and independent package distribution remain future generator work.

## Manifest contract

`schema_version` is currently `1`. The `web-next-auth` blueprint requires exactly the `web-bff-core` and `web-session-core` modules in that order. Product slug, display name, npm package name, and package specifications are validated before any output file is created.

Repository-local `file:` package specifications are used only by the proof manifest so CI can validate unpublished EXPERIMENTAL modules. A future product-repository flow must use an approved package distribution mechanism rather than assuming the DevForge source checkout is adjacent.

## Usage

```bash
node generator/generate.mjs \
  --manifest generator/manifests/web-auth-proof.json \
  --output .generated/generated-auth-proof
```

The output directory must be absent or empty. The generator refuses to overwrite non-empty product directories.

## Security and determinism

- unknown manifest keys fail closed;
- unsupported blueprint/module combinations fail closed;
- product identifiers are bounded and validated;
- template paths cannot be absolute, empty-segmented, backslash-based, or contain `.` / `..` traversal segments;
- unknown/unresolved template tokens fail closed;
- output files use exclusive creation;
- no timestamp or random identifier is written into generated output;
- no secrets, production domains, or credentials are generated.

## Proof gate

The generator CI must:

- run generator unit tests;
- generate the proof product twice and compare the outputs byte-for-byte;
- build the reusable web packages;
- install the generated product;
- run strict TypeScript checks;
- complete a Next.js production build;
- migrate and start the real FastAPI `backend-core` with PostgreSQL and Redis;
- start the generated product as a production Next.js server;
- run Chromium through generated registration, login, current-session read, logout, and post-logout rejection;
- verify the opaque backend session credential is not exposed in browser-visible JSON, DOM, `document.cookie`, localStorage, or sessionStorage.

The repository-local runtime proof path is:

```text
Chromium
  -> generated Next.js product / BFF
     -> FastAPI backend-core
        -> PostgreSQL
        -> Redis
```

Passing this gate proves deterministic generation plus a real-browser generated-product runtime composition against reusable backend infrastructure. The runtime proof intentionally uses loopback HTTP in CI; TLS/ingress forwarding-header security is covered separately by the production-like web ingress proof.

This still does not complete the roadmap generator/pilot gates. Independent product-repository package distribution, a second materially different generated product, real staging/production deployment evidence, and repeated reuse remain open.
