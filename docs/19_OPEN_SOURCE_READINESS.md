# Open-Source Readiness

Status: PUBLIC SOURCE HARDENING — REPOSITORY POLICY READY; FORMAL RELEASE EVIDENCE STILL REQUIRED

## Licensing model

DevForge-owned source is prepared for distribution under the Apache License, Version 2.0. The root `LICENSE` contains the license text and `NOTICE` contains DevForge attribution. Reusable package directories carry their own copies so independently distributed package artifacts do not depend on a parent monorepo checkout for license information.

Third-party dependencies remain under their upstream licenses. `THIRD_PARTY_NOTICES.md` records the current direct/runtime and infrastructure boundaries; every formal release must verify the exact transitive dependency/license inventory actually shipped.

## Public repository security baseline

- no secrets, private keys, production credentials, or customer data are allowed in source;
- remote GitHub Actions must be pinned to full reviewed commit SHAs;
- current infrastructure uses an OSI-open-source Valkey server baseline instead of Redis Community Edition 7.4 server images;
- vulnerabilities should be reported privately as described in `SECURITY.md`;
- external code must pass `docs/03_OSS_INTAKE_POLICY.md` before adoption;
- `scripts/verify_open_source_readiness.py` machine-checks the repository-level invariants above.

## Completed source-history security evidence

On exact head `a594a1830aac4528ea753e5fd3d21ed20b03fca2`, Gitleaks 8.24.3 ran an all-refs Git-history scan over the repository heads/tags fetched by CI and scanned 406 reachable commits with zero remaining findings. The only earlier hit was verified as the pinned SHA-256 checksum for OpenAPI Generator, not a credential, and is suppressed only by an exact `commit:path:rule:line` fingerprint. The readiness guard rejects broad or malformed Gitleaks-ignore entries.

This closes the repository-side full Git-history secret-scan requirement for that exact head. It does not authorize rewriting historical author metadata, and it does not replace release-time revalidation at the exact release SHA.

## Valkey migration boundary

The service name and application configuration continue to use the existing `redis`/`DEVFORGE_REDIS_URL` compatibility contract so backend code does not need a product-level API migration. The server implementation is Valkey 7.2.14, which speaks the Redis-compatible RESP protocol used by redis-py.

This repository has not performed a real production or staging data migration. Existing Redis Community Edition 7.4 RDB/AOF persistence must not be assumed compatible with Valkey 7.2. Any real host with existing Redis 7.4 data requires an explicit backup, compatibility check, validated migration path, and rollback plan before changing the server implementation.

## What this does not authorize

Making source available under Apache-2.0 does not by itself authorize:

- merging open pull requests;
- publishing packages or container images;
- creating a production release;
- deploying real staging or production;
- claiming a generated product is production-ready;
- relicensing third-party dependencies.

Those actions remain subject to DevForge review and release gates.

## Remaining formal-release checks

Before the first tagged/public package release:

1. Re-run the full current-tree, PR/range, and all-refs Git-history secret scan at the exact release SHA.
2. Confirm GitHub private vulnerability reporting is enabled or document an equivalent private contact channel.
3. Produce an exact transitive SBOM/license report for every distributed package/container.
4. Verify all required third-party license/NOTICE material is included in each release artifact.
5. Confirm maintainers have redistribution rights for any generalized internal-donor material promoted into the release.
6. Review public branch protection/rulesets and least-privilege workflow permissions.
7. Re-run current build, test, security, generator, staging-candidate, and open-source-readiness gates at the exact release SHA.

Until those release-time checks are recorded, the repository may be publicly reusable under its source license, but no formal Production Candidate or production release claim should be inferred.
