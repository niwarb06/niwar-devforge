# Staging operability evidence

Status: **REPOSITORY OPERABILITY FRAMEWORK; REAL HOST EVIDENCE STILL REQUIRED**

This document adds provider-neutral monitoring/alert and rollback-drill controls for the generated Web staging pilot. It does not authorize production, does not merge the stacked PRs, and does not claim that a real staging alert or rollback drill has already occurred.

## 1. External health monitor

`observability/staging_monitor.py` is intentionally independent from Docker and the application process. It probes the real public HTTPS boundary from the host/network environment and verifies two paths:

1. `/` must return HTTP 200.
2. `/api/auth/me` must return HTTP 200 or 401. A 401 is healthy for an anonymous request and proves that the Web/BFF -> backend authentication path is reachable.

Production-like URLs must use HTTPS. Plain HTTP is accepted only for explicit loopback tests with `--allow-insecure-loopback`.

The monitor stores:

- a private state file used to suppress duplicate firing alerts;
- a private JSONL event log with timestamp, status, previous status, origin, and a bounded reason;
- no passwords, session tokens, response bodies, alert bearer values, or alert endpoint query values.

On a state transition it sends a provider-neutral JSON POST to `STAGING_ALERT_WEBHOOK_URL`:

- `firing` when the public/auth path becomes unhealthy;
- `resolved` when it recovers;
- `test` for an explicit alert-delivery drill.

`STAGING_ALERT_WEBHOOK_BEARER` is optional and never written to the event log.

## 2. Hardened systemd unit

The example unit is `systemd/niwar-devforge-staging-monitor.service`.

Host preparation, performed by an authorized staging operator:

```bash
sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin devforge-monitor || true
sudo install -d -m 0750 -o devforge-monitor -g devforge-monitor /var/lib/niwar-devforge-monitor
sudo install -d -m 0750 -o devforge-monitor -g devforge-monitor /var/log/niwar-devforge-monitor
sudo install -d -m 0755 /opt/niwar-devforge-monitor
sudo install -m 0755 infrastructure/staging/observability/staging_monitor.py \
  /opt/niwar-devforge-monitor/staging_monitor.py
sudo install -d -m 0750 /etc/niwar-devforge
sudo install -m 0600 infrastructure/staging/systemd/staging-monitor.env.example \
  /etc/niwar-devforge/staging-monitor.env
sudo install -m 0644 infrastructure/staging/systemd/niwar-devforge-staging-monitor.service \
  /etc/systemd/system/niwar-devforge-staging-monitor.service
```

Edit `/etc/niwar-devforge/staging-monitor.env` on the host only and set the real owned staging origin and the real alert webhook destination. Never commit those values.

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now niwar-devforge-staging-monitor.service
sudo systemctl status niwar-devforge-staging-monitor.service --no-pager
```

The service has no Docker socket access and does not need application credentials. It runs with `NoNewPrivileges`, a read-only system view, a private temporary directory, restricted address families, and write access only to its state/event directories.

## 3. Alert-delivery drill

A real Production Candidate needs demonstrated alert delivery, not merely configured alert code.

After the monitor environment is configured, run an explicit drill as the monitor identity:

```bash
set -a
. /etc/niwar-devforge/staging-monitor.env
set +a
sudo -u devforge-monitor \
  STAGING_ALERT_WEBHOOK_URL="$STAGING_ALERT_WEBHOOK_URL" \
  STAGING_ALERT_WEBHOOK_BEARER="${STAGING_ALERT_WEBHOOK_BEARER:-}" \
  /usr/bin/python3 /opt/niwar-devforge-monitor/staging_monitor.py \
    --origin "$STAGING_PUBLIC_ORIGIN" \
    --state-file /var/lib/niwar-devforge-monitor/state.json \
    --event-log /var/log/niwar-devforge-monitor/events.jsonl \
    --alert-drill
```

The drill is evidence only when the external destination confirms receipt and the operator records the timestamp/provider destination identifier without storing any secret credential in the repository.

## 4. Release metadata guard

`scripts/release_guard.py` defines a strict machine-readable staging release metadata record. A valid record contains exactly:

- schema version;
- exact lowercase 40-character source SHA;
- immutable backend GHCR `@sha256:` image;
- immutable Web GHCR `@sha256:` image;
- database migration/schema head;
- GitHub Actions workflow run ID;
- UTC deployment timestamp.

Mutable image tags are rejected.

## 5. Rollback drill boundary

`scripts/rollback-release.sh` performs an **application-image rollback only**. It deliberately refuses to downgrade the database schema or infrastructure definition.

Before changing images it:

1. validates the previous release metadata;
2. reads the current live Alembic schema head;
3. requires an exact match with the target previous release metadata;
4. blocks immediately on any mismatch;
5. hands control to the existing `deploy-release.sh`, which takes a fresh backup, uses temporary registry authentication, pulls immutable images, starts with `--no-build`, and runs health checks.

This conservative rule means a release that introduced a migration cannot be automatically rolled back to an older application. Such a case requires a migration-specific compatibility/recovery review and explicit approval.

A real rollback drill should use a previous known-good staging release and then re-promote the current known-good release after validation. Record the source SHA/image digests, schema head, pre-drill backup checksum, drill timestamps, health/E2E outcomes, and operator.

## 6. Log evidence

The staging Caddy configuration emits structured JSON access logs and backend-core emits bounded application logs. The monitor adds a separate host-side JSONL health-event stream outside the application containers.

This framework still **does not claim centralized application-log shipping**. Before Production Candidate status, the real staging deployment must demonstrate that application/ingress logs are retained or shipped outside ephemeral container stdout according to the chosen hosting environment, with access/retention controls documented.

## 7. What CI proves vs. what remains real-host evidence

Repository CI can prove:

- monitor URL validation and secret-safe transition behavior;
- alert firing de-duplication and recovery resolution using an isolated local sink;
- explicit alert-drill payload delivery to a test sink;
- immutable release metadata validation;
- schema mismatch blocks the rollback guard;
- shell/Python syntax and regression safety.

Repository CI cannot prove:

- the real owned staging hostname is reachable;
- the real external alert destination received a drill;
- the monitor stays healthy over time on the real host;
- centralized application logs are retained/shipped in the real environment;
- a real rollback drill completed against two known-good immutable staging releases.

Do not mark Phase 8 or Production Candidate complete until those real-host evidence items are recorded alongside the real staging deployment evidence.
