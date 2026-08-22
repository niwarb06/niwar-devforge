# Web Pilot — Production Candidate Evidence Gate

Status: **OPEN / NOT REACHED**

This document defines the evidence required before the generated Web Auth pilot may be recorded as a DevForge Production Candidate. It does not authorize production deployment.

Machine-readable state: `docs/evidence/web-production-candidate.json`

Machine verifier: `scripts/verify_web_production_candidate_evidence.py`

## Repository evidence already available

The stacked Web pilot now has repository-backed proof for deterministic generation, strict build/type checks, real backend browser E2E, production-like TLS ingress, isolated staging topology, dependency/secret scanning, health checks, and PostgreSQL backup/restore verification.

PR #27 adds a guarded real-staging release path, but repository CI alone cannot claim a real Production Candidate because it has not exercised an owned staging host/domain or deployed monitoring/rollback evidence.

## Fail-closed Production Candidate state

`docs/evidence/web-production-candidate.json` intentionally starts as `open_not_reached` with null/open evidence fields. CI rejects a premature transition to `production_candidate` unless all required evidence is present and internally consistent.

A valid completed record requires:

- exact lowercase 40-character staged source SHA;
- real HTTPS staging origin, excluding example/test/local origins;
- immutable GHCR backend and Web `@sha256:` image references;
- successful real-staging workflow run ID;
- public TLS, service isolation, real browser E2E, and backup/restore all marked `success`;
- deployed external log collection;
- public uptime and backend/service health monitoring;
- demonstrated alert delivery with an evidence reference;
- successful rollback drill to a materially previous immutable release;
- migration head, backup checksum reference, release notes reference, and operator reference;
- Production Candidate timestamp and duration recomputed from the original Web pilot PR open time.

## Release metadata

After a real staging deployment, record release metadata on the host with:

```bash
bash infrastructure/staging/scripts/write-release-metadata.sh \
  <release-dir> \
  <source-sha> \
  <backend-image@sha256:digest> \
  <web-image@sha256:digest> \
  <workflow-run-id> \
  <backup-checksum-reference>
```

The script queries the live Alembic migration head and atomically writes `release-metadata.json` with mode `0600`. It records no database password, Redis password, SSH key, token, or customer data.

## Monitoring and alert delivery

Use the provider-neutral monitoring contract in `infrastructure/staging/monitoring/README.md`.

A real monitor should execute or wrap:

```bash
STAGING_PUBLIC_ORIGIN=https://<owned-staging-host> \
  bash infrastructure/staging/scripts/monitor-staging.sh
```

To prove alert delivery without breaking staging, run the synthetic failure mode through the actual monitoring path:

```bash
STAGING_PUBLIC_ORIGIN=https://<owned-staging-host> \
DEVFORGE_MONITOR_FORCE_FAILURE=1 \
  bash infrastructure/staging/scripts/monitor-staging.sh
```

The probe exits `42` and emits a unique alert-drill marker. The monitoring provider/on-call destination must receive the corresponding event. Repository CI verifies the synthetic failure behavior but cannot claim delivery to a real person/service.

## Rollback drill

Rollback is application-only and deliberately fail-closed:

```bash
bash infrastructure/staging/scripts/rollback-release.sh \
  <current-release-dir> \
  <previous-release-dir> \
  <backup-dir> \
  ROLLBACK-STAGING
```

The script:

1. requires explicit rollback confirmation;
2. requires the previous application images to be immutable GHCR digests;
3. reads the previous release migration head from `release-metadata.json`;
4. compares it to the current live database migration head;
5. **blocks rollback if schema heads differ** and never performs an automatic schema downgrade;
6. creates a fresh pre-rollback PostgreSQL backup + checksum;
7. pulls the previous immutable application images and starts them with `--no-build`;
8. requires health validation to pass after rollback.

A real Production Candidate evidence record may mark the rollback drill successful only after this is exercised against two actual staged releases with distinct source SHAs and retained evidence.

## Remaining real-world sequence

1. Explicitly review and merge the required stacked PRs; no automatic merge is allowed.
2. Configure the protected GitHub `staging` environment, owned DNS, staging VPS, verified SSH host key, host secrets, and read-only GHCR pull identity.
3. Manually run the guarded real-staging release workflow against the exact `main` SHA.
4. Record the real release metadata.
5. Configure external logs, uptime/service monitoring, and prove alert delivery using the synthetic drill.
6. Deploy a later known-good staging revision and perform a rollback drill to the earlier immutable release while schema heads remain compatible.
7. Update `web-production-candidate.json` with real evidence and run the verifier.
8. Only after all Definition of Done gates pass may the Web pilot be recorded as Production Candidate.

Production deployment still requires separate explicit approval.
