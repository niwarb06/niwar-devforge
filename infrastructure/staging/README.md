# Web staging deployment runbook

Status: **STAGING-READY PROOF; NOT A PRODUCTION DEPLOYMENT**

This directory defines the first deployment-oriented proof for the generated `web-next-auth` pilot. It is designed to satisfy the repository staging, isolation, TLS, health, backup/restore, and rollback evidence gates before anyone requests a production release.

## Topology

```text
Internet / browser
       |
       | HTTPS :443
       v
     Caddy  -------------------------- public edge
       |
       | HTTP on private edge network
       v
Generated Next.js Web/BFF
       |
       | HTTPS, private CA, service network
       v
     Caddy internal backend endpoint
       |
       | private service network
       v
FastAPI backend-core
       |                 |
       | data network    | data network
       v                 v
 PostgreSQL            Redis
```

Only Caddy publishes host ports. Web, backend, PostgreSQL, and Redis have no host port mapping. The `service` and `data` Docker networks are marked `internal`.

The backend trusts forwarded client addresses only from the fixed Caddy service-network address `172.30.20.2/32`. The public Caddy route removes any client-supplied `X-DevForge-Ingress-Client-IP` and replaces it with Caddy's observed client address. The generated BFF validates that single IP literal before translating it to `X-Forwarded-For` for credential endpoints.

## TLS boundaries

- Browser -> Caddy: `infrastructure/staging/Caddyfile` uses Caddy automatic HTTPS for the configured owned staging hostname.
- Web/BFF -> backend ingress: `https://backend.internal` uses Caddy's internal CA. Only the public root certificate is exported to the web container; the internal CA private key is never mounted there.
- Backend -> PostgreSQL/Redis currently relies on isolated Docker data networking rather than application-layer TLS. This is acceptable only for this single-host staging topology. A multi-host deployment requires TLS-authenticated database/cache transport or an equivalent private network control reviewed for that deployment.

`Caddyfile.ci` uses the internal CA for the public hostname as well, solely so CI can prove the topology without an external DNS/ACME dependency.

## Prerequisites for a real staging host

1. An owned staging DNS name whose A/AAAA records point to the deployment host.
2. TCP 80/443 and UDP 443 reachable by Caddy as required for automatic HTTPS/HTTP3. Do not expose backend, PostgreSQL, Redis, or the generated web service directly.
3. Docker Engine with Docker Compose v2.
4. A host firewall that permits only the intended management path plus public 80/443.
5. No upstream CDN/load balancer unless its exact trusted proxy ranges and header behavior are explicitly configured and revalidated. Never enable broad/private proxy trust merely to make client-IP forwarding work.

## Create staging-only secrets

Create secret files outside the repository:

```bash
sudo install -d -m 0700 /srv/niwar-devforge/staging/secrets
openssl rand -hex 32 | sudo tee /srv/niwar-devforge/staging/secrets/postgres_password >/dev/null
openssl rand -hex 32 | sudo tee /srv/niwar-devforge/staging/secrets/redis_password >/dev/null
sudo chmod 0600 /srv/niwar-devforge/staging/secrets/*
```

Never commit these files. A managed secret store may replace host files if the deployment platform supports it and preserves the same least-privilege boundary.

## Configure

Copy `.env.example` to an ignored host-only file and set the real staging hostname/origin and secret paths:

```bash
cp infrastructure/staging/.env.example /srv/niwar-devforge/staging/staging.env
chmod 0600 /srv/niwar-devforge/staging/staging.env
```

Validate interpolation before starting anything:

```bash
docker compose \
  --env-file /srv/niwar-devforge/staging/staging.env \
  -f infrastructure/staging/compose.yml \
  config --quiet
```

For a release candidate, prefer immutable registry image digests in `STAGING_BACKEND_IMAGE` and `STAGING_WEB_IMAGE`. Mutable `:local` images are for the repository proof only.

## Start / update staging

Take a database backup before replacing an existing staging release. Then build/pull the intended exact revision and start the stack:

```bash
docker compose \
  --env-file /srv/niwar-devforge/staging/staging.env \
  -f infrastructure/staging/compose.yml \
  up -d --build
```

`migrate` is a one-shot service. `backend` starts only after migrations complete successfully. `web` starts only after backend health passes and Caddy's internal public CA certificate has been safely exported.

## Health and smoke validation

```bash
set -a
. /srv/niwar-devforge/staging/staging.env
set +a
bash infrastructure/staging/scripts/healthcheck.sh
```

Required evidence on a real staging host also includes the browser authentication flow over the real certificate: register -> login -> current session/profile -> logout -> post-logout rejection, with a Secure + HttpOnly session cookie and no opaque backend token visible to browser JavaScript.

## Backup and restore verification

Create an atomic PostgreSQL custom-format backup with a checksum:

```bash
backup="$(bash infrastructure/staging/scripts/backup.sh /srv/niwar-devforge/staging/backups)"
```

Prove that the backup is restorable **without overwriting live staging data**:

```bash
bash infrastructure/staging/scripts/verify-restore.sh "$backup"
```

The restore verifier creates a temporary database, restores into it, verifies the Alembic schema head, and drops the temporary database on exit.

Redis contains rate-limit/session state and is configured with AOF persistence, but PostgreSQL remains the authoritative durable user/profile data store for this pilot. A product that places authoritative business data in Redis must define a separate backup/restore policy.

## Rollback procedure

Before release, record:

- exact Git commit;
- backend image digest;
- web image digest;
- migration head;
- backup path/checksum;
- release timestamp and operator.

If application rollback is required:

1. Stop further rollout and take a fresh backup if the database is healthy.
2. Review migrations introduced by the failed release. **Do not blindly downgrade schema.** If migrations are not backward compatible, use the documented migration-specific recovery plan and obtain explicit approval for any destructive change.
3. Set `STAGING_BACKEND_IMAGE` and `STAGING_WEB_IMAGE` to the previous known-good immutable digests.
4. Run `docker compose ... up -d`.
5. Run `healthcheck.sh` and the critical browser flow again.
6. Record the incident, rollback revision, database state, and follow-up action.

Production rollback must never depend on an untested database restore. This staging runbook intentionally includes restore verification so that a future production release can cite evidence instead of configuration alone.

## Logging and monitoring

- Caddy emits structured JSON access logs to stdout in the real staging `Caddyfile`.
- backend-core emits application logs to stdout/stderr according to its configured log level.
- Docker health checks cover backend, PostgreSQL, and Redis; the operator health script also checks the public web origin.

For a real staging Production Candidate, stdout logs must be collected by an external logging/monitoring system and alerts must be demonstrated for at least public endpoint failure and backend health failure. Repository CI cannot substitute for deployed alert-delivery evidence.

## Production Candidate evidence still required

A green repository staging CI is necessary but not sufficient. Before marking the Web pilot Production Candidate, record all of the following against a real staging deployment:

- owned staging hostname and publicly valid certificate;
- actual host/network firewall evidence and no direct backend/database/cache exposure;
- exact immutable image digests and source revision;
- deployment secret source/permissions with no committed secret;
- dependency and secret scan results with Critical/exploitable High findings resolved or explicitly blocking;
- real staging browser E2E result;
- real backup + non-destructive restore verification result;
- external log collection, uptime/health monitoring, and alert-delivery evidence;
- release notes and tested rollback procedure;
- Production Candidate timestamp only after all applicable Definition of Done gates pass.

No production deployment is authorized by this runbook or its CI workflow.
