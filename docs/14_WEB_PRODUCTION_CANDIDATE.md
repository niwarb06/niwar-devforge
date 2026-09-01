# Web Pilot — Production Candidate Evidence Gate

Status: **OPEN / NOT REACHED**

This document defines the fail-closed evidence contract required before the generated Web Auth pilot may be recorded as a Niwar DevForge Production Candidate. It does **not** authorize a production deployment.

Machine-readable state: `docs/evidence/web-production-candidate.json`

Machine verifier: `scripts/verify_web_production_candidate_evidence.py`

CI proof: `.github/workflows/production-candidate-evidence-ci.yml`

## Why this exists

`docs/13_PILOT_PROOF_METRICS.md` already proves the generated Web Auth and Flutter pilots and deliberately leaves the Production Candidate duration open. The repository now also contains a real-staging release path, provider-neutral staging monitoring, immutable release metadata, guarded rollback, backup/restore controls, and an always-run required PR gate.

Those controls are necessary but they are not, by themselves, proof that a real owned staging environment was deployed and operated successfully. This evidence contract prevents repository-only CI from silently turning that missing real-world proof into a Production Candidate claim.

## Current control plane used by this contract

The verifier is intentionally coupled to the current reviewed staging controls on `main`:

- `infrastructure/staging/REAL_STAGING_RELEASE.md`
- `infrastructure/staging/OPERABILITY.md`
- `infrastructure/staging/observability/staging_monitor.py`
- `infrastructure/staging/scripts/record-release-meta.sh`
- `infrastructure/staging/scripts/release_guard.py`
- `infrastructure/staging/scripts/rollback-release.sh`

If these controls disappear or lose the reviewed alert-delivery, immutable-image, release-metadata, or schema-compatibility markers, the evidence verifier fails closed.

## Evidence state

The JSON evidence begins as `open_not_reached`. While it is open:

- the candidate timestamp and duration must be null;
- no staging origin may be claimed;
- the release record must be empty;
- every real-staging and monitoring gate must remain `open`;
- the rollback drill must remain `open`;
- no real-world evidence reference may be claimed.

Changing only the status field to `production_candidate` is intentionally rejected by CI.

## Requirements for a valid Production Candidate claim

A completed record is accepted only when all of the following are present and internally consistent.

### Real staged release

- a real public HTTPS staging origin, not localhost, test/example domains, or a private/reserved IP;
- exact lowercase 40-character source SHA;
- immutable GHCR backend and Web images using `@sha256:` digests;
- the live database schema head recorded by the current release metadata path;
- the successful real-staging workflow run ID;
- the deployment timestamp from the staged release record;
- a retained release-metadata reference;
- a retained backup checksum reference;
- release-notes and operator evidence references;
- public TLS, service isolation, real browser E2E, and backup/restore all recorded as `success`.

The release metadata must be produced through the current control plane:

```bash
bash infrastructure/staging/scripts/record-release-meta.sh \
  <release.env> \
  <release.meta.json> \
  <source-sha> \
  <backend-image@sha256:digest> \
  <web-image@sha256:digest> \
  <workflow-run-id>
```

The script delegates schema/image/run validation to `release_guard.py`.

### Monitoring and alert delivery

The current provider-neutral monitor must be deployed against the owned HTTPS staging origin. The evidence record requires:

- external log collection;
- public uptime monitoring;
- backend/service health monitoring;
- a demonstrated alert-delivery drill;
- a retained monitoring evidence reference.

The current monitor supports an explicit alert-delivery drill through the real webhook path:

```bash
STAGING_ALERT_WEBHOOK_URL=https://<alert-endpoint> \
python3 infrastructure/staging/observability/staging_monitor.py \
  --origin https://<owned-staging-host> \
  --state-file /var/lib/niwar-devforge/staging-monitor-state.json \
  --event-log /var/log/niwar-devforge/staging-monitor-events.jsonl \
  --alert-drill
```

Repository CI can prove that the drill control exists and that the evidence schema is fail-closed. It cannot claim that an external provider or operator actually received the alert; the evidence reference must come from the real staging operation.

### Rollback drill

A Production Candidate requires a successful rollback drill against two materially different immutable staged releases.

The current rollback entry point is:

```bash
bash infrastructure/staging/scripts/rollback-release.sh \
  <previous-release.env> \
  <previous-release.meta.json> \
  <backup-dir> \
  <registry-user>
```

The current rollback path validates the previous release metadata, requires the live schema head to match the rollback target, then delegates to the guarded release path, which takes a fresh pre-change backup and performs health validation. It never performs an automatic schema downgrade.

The evidence record must retain:

- the materially previous source SHA;
- previous immutable backend and Web image digests;
- the pre-rollback backup reference;
- rollback completion time;
- an operator/evidence reference proving the drill was exercised against real staging.

### Production Candidate duration

The measured duration starts at the already-recorded Web pilot PR opening time:

`2026-08-22T15:26:03Z`

The verifier recomputes `seconds_from_pilot_pr_open` from that timestamp and rejects an invented or inconsistent duration.

## CI boundary

`Production Candidate Evidence CI` does four things:

1. checks out the exact PR head with full history;
2. validates syntax of the current evidence and staging control scripts;
3. verifies the `OPEN / NOT REACHED` baseline;
4. proves that a premature `production_candidate` status change fails closed.

The workflow uses the repository-approved immutable GitHub Action SHAs. It is intentionally path-filtered and is **not** the globally required status check; `required-pr-gate` remains the always-run required check for all PRs.

## Remaining real-world sequence

1. Keep the JSON state `open_not_reached`.
2. Configure an owned staging host/domain and the protected staging environment.
3. Manually run the guarded real-staging release workflow against an exact `main` SHA.
4. Retain the real release metadata and backup checksum evidence.
5. Run external logs/uptime/service monitoring and prove real alert delivery.
6. Deploy a later known-good immutable staging release.
7. Exercise the guarded rollback drill to the earlier compatible release and retain evidence.
8. Update `web-production-candidate.json` with the real evidence.
9. Run the verifier and review the resulting Production Candidate duration.
10. Only then may the Web pilot be recorded as a Production Candidate.

Production deployment remains a separate action requiring explicit human authorization.
