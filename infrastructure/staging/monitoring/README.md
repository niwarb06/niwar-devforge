# Staging monitoring and alert evidence contract

Status: **READY FOR REAL-HOST CONFIGURATION; ALERT DELIVERY NOT YET PROVEN**

The Web Production Candidate requires deployed monitoring evidence, not only container health checks in repository CI.

## Required deployed signals

A real staging monitoring system must cover at least:

1. **Public HTTPS availability** — probe the owned staging origin over normal certificate validation.
2. **Backend/service health** — execute the host-side DevForge health probe so backend, PostgreSQL, Redis, and the public path are checked together.
3. **External log collection** — collect Caddy structured JSON logs and backend stdout/stderr outside the containers/host process lifetime.
4. **Alert delivery** — demonstrate that a failed staging monitor reaches the configured human/on-call destination.

The monitoring provider is intentionally not hard-coded. The provider must run or wrap:

```bash
STAGING_PUBLIC_ORIGIN=https://<owned-staging-host> \
  bash infrastructure/staging/scripts/monitor-staging.sh
```

A zero exit code means the probe passed. Any non-zero exit code is alert-worthy.

## Safe alert-delivery drill

Do **not** intentionally break the application to test alert routing. Use the synthetic failure switch:

```bash
STAGING_PUBLIC_ORIGIN=https://<owned-staging-host> \
DEVFORGE_MONITOR_FORCE_FAILURE=1 \
  bash infrastructure/staging/scripts/monitor-staging.sh
```

The command exits `42` and prints a unique `FORCED_MONITOR_FAILURE devforge-alert-drill-<UTC timestamp>` marker. The configured monitoring/alerting system must observe that failure and deliver an alert. Record the provider incident/event/reference containing the same drill marker in `docs/evidence/web-production-candidate.json`.

The drill switch is a probe-process behavior only. It does not change application state, stop containers, alter traffic, or mutate data.

## Evidence required before marking success

Record evidence only after all of these are true on the real staging deployment:

- public uptime monitor enabled and passing;
- backend/service health monitor enabled and passing;
- Caddy/backend logs visibly arriving in the external collector;
- one synthetic failure drill delivered to the configured human/on-call destination;
- the alert/event reference is retained and can be reviewed.

Repository CI may validate this monitoring contract and the synthetic failure behavior, but it **cannot** set the monitoring evidence to `success` by itself.
