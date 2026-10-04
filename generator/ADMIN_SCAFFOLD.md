# Admin scaffold foundation

Status: EXPERIMENTAL

Phase 5 requires the generator to emit an Admin scaffold. DevForge's canonical architecture defines both Web and Admin on Next.js + TypeScript, so this foundation intentionally reuses the existing `web-next-auth` blueprint instead of duplicating the same authentication template under a second blueprint name.

The proof manifest is `generator/manifests/admin-auth-proof.json`. It gives the generated product an explicit Admin identity while keeping the existing, tested browser credential boundary from `web-bff-core` and session revalidation from `web-session-core`.

Generate the proof with:

```bash
node generator/generate.mjs \
  --manifest generator/manifests/admin-auth-proof.json \
  --output .generated/generated-admin-proof
```

The output includes the existing deterministic Next.js scaffold, environment example, auth route wrappers, test skeleton, generated CI, local Docker/dev setup, canonical database migrations, and `.devforge-generation.json` provenance record.

## Scope boundary

This is the minimal Admin scaffold foundation only. It does not invent Admin dashboards, CRUD screens, role/permission policy, broader authorization, pack runtime composition, provider adapters, standalone package distribution, deployment, release, staging, or production behavior.

`Generator Admin Auth CI` proves that the Admin proof is generated twice byte-identically and that the generated product installs, runs its generated test skeleton, typechecks, and builds against the existing reusable Web auth modules.
