# Real staging release gate

Status: **READY FOR CONFIGURATION; NO REAL STAGING DEPLOYMENT HAS BEEN EXECUTED BY THIS DOCUMENT**

This runbook turns the CI-only staging proof into a guarded real-host staging deployment path. It does not authorize production and it does not bypass the repository merge/review rules.

## Required GitHub environment

Create a protected GitHub environment named `staging`. Require human approval for deployment if the repository plan supports environment protection rules.

Configure these non-secret environment variables:

| Variable | Example | Purpose |
| --- | --- | --- |
| `STAGING_HOST` | `staging.example.com` | Owned public DNS name. Must terminate publicly trusted TLS on port 443. |
| `STAGING_SSH_HOST` | `203.0.113.10` or `staging-host.example.com` | SSH target. IPv4/DNS form is supported by the current gate. |
| `STAGING_SSH_PORT` | `22` | Optional SSH port; defaults to 22. |
| `STAGING_SSH_USER` | `deploy` | Least-privilege deployment account. |
| `STAGING_REMOTE_ROOT` | `/srv/niwar-devforge/staging/releases` | Per-release immutable deployment directories. |
| `STAGING_BACKUP_DIR` | `/srv/niwar-devforge/staging/backups` | PostgreSQL backup directory outside release folders. |
| `STAGING_POSTGRES_PASSWORD_FILE` | `/srv/niwar-devforge/staging/secrets/postgres_password` | Existing host-only secret file. |
| `STAGING_REDIS_PASSWORD_FILE` | `/srv/niwar-devforge/staging/secrets/redis_password` | Existing host-only secret file. |
| `STAGING_LOGIN_IP_LIMIT` | `10` | Optional real staging login-IP limit used by both runtime and E2E; defaults to 10. |

Configure these GitHub environment secrets:

| Secret | Purpose |
| --- | --- |
| `STAGING_SSH_PRIVATE_KEY` | Private key for the dedicated deployment account. Never commit it. |
| `STAGING_SSH_KNOWN_HOSTS` | Pre-verified `known_hosts` line(s) for the SSH target. The workflow never disables host-key checking. |
| `STAGING_GHCR_USER` | Read-only GHCR identity used by the staging host. |
| `STAGING_GHCR_TOKEN` | Read-only GHCR token delivered only over the verified SSH channel. |

The workflow uses the repository `GITHUB_TOKEN` only to publish application images to GHCR. It resolves the pushed images to immutable `@sha256:` references before deployment. The remote read-only GHCR credential is placed in a temporary Docker configuration for the pull and removed immediately after use; it is not intentionally persisted in the deployment account's normal Docker config.

## Host preparation

The deployment account needs Docker/Compose access without becoming a general-purpose root shell. Configure the host firewall so only the intended management path and public TCP 80/443 (plus UDP 443 if HTTP/3 is enabled) are reachable. Do not publish ports 3000, 8000, 5432, or 6379.

Create the release and backup roots with ownership that permits the deployment account to create release directories and backups. Keep the password files outside release directories.

The backend/migration image uses fixed UID/GID `10001:10001`, so the password files must be group-readable by GID 10001 and not world-readable. Run the following while logged in as the intended deployment account so `$(id -u)` records that operator as the owner:

```bash
sudo install -d -m 0750 -o "$(id -u)" -g 10001 /srv/niwar-devforge/staging/secrets
openssl rand -hex 32 | sudo tee /srv/niwar-devforge/staging/secrets/postgres_password >/dev/null
openssl rand -hex 32 | sudo tee /srv/niwar-devforge/staging/secrets/redis_password >/dev/null
sudo chown "$(id -u):10001" \
  /srv/niwar-devforge/staging/secrets/postgres_password \
  /srv/niwar-devforge/staging/secrets/redis_password
sudo chmod 0640 \
  /srv/niwar-devforge/staging/secrets/postgres_password \
  /srv/niwar-devforge/staging/secrets/redis_password
```

The release workflow runs `validate-host-secrets.sh` before migrations or application startup and fails closed if either file is missing, empty, symlinked, not mode `0640`, or not group `10001`.

## SSH trust

Build `STAGING_SSH_KNOWN_HOSTS` from a separately verified host-key fingerprint. Do not obtain the key and trust it in the same unauthenticated deployment step. Re-verify the fingerprint out of band after host rebuilds or SSH host-key rotation.

## Release authorization

The manual workflow is `.github/workflows/real-staging-release.yml`.

It requires:

1. an exact lowercase 40-character `source_sha`;
2. `confirm = DEPLOY-STAGING`;
3. the source SHA to be reachable from `origin/main`;
4. the protected `staging` GitHub environment configuration above.

This intentionally prevents deploying an unmerged PR head as the formal Production Candidate staging revision. The stacked PRs must be reviewed and merged only with explicit user approval before this gate can deploy their resulting main commit.

## What the workflow proves

For an authorized dispatch, the gate:

1. checks out the exact main-reachable source SHA;
2. builds backend and generated Web images from that revision;
3. publishes `niwar-devforge-backend-staging` and `niwar-devforge-web-staging` packages in the repository owner's GHCR namespace and resolves immutable `@sha256:` digests;
4. validates SSH trust and deployment inputs;
5. uploads a release bundle into a new per-run remote release directory;
6. validates host secret metadata;
7. authenticates to GHCR through a temporary Docker config, takes a pre-deploy PostgreSQL backup when a staging database already exists, pulls the immutable application images, starts the isolated Compose topology with `--no-build`, and removes the temporary registry config;
8. runs health checks over normal certificate validation;
9. verifies the public certificate/security headers and fails if ports 3000/8000/5432/6379 are publicly reachable;
10. runs the audited Chromium register/login/session/logout and trusted-ingress spoof/rate-limit proof;
11. creates a post-deploy PostgreSQL backup and proves a non-destructive restore into a temporary database;
12. records the exact source SHA, immutable application image digests, public origin, release directory, and workflow run ID in the GitHub Actions job summary.

The workflow does **not** automatically roll back on failure because migrations may introduce compatibility boundaries. It captures remote state and logs; rollback remains an explicit reviewed operation using the previous known-good immutable image digests and the migration-specific recovery plan.

## Still required before Production Candidate

A successful real-staging deployment closes many repository proof gaps, but Production Candidate status still requires repository evidence for:

- deployed log collection outside container stdout;
- uptime/health monitoring and demonstrated alert delivery;
- a recorded rollback drill against a known-good previous release;
- release notes containing exact source/image/migration/backup evidence;
- review of any remaining dependency or infrastructure-image findings;
- explicit production deployment approval.

Do not mark Phase 8 complete merely because the workflow exists. Record evidence from an actual successful staging run and update the pilot metrics/Production Candidate timestamp only when the Definition of Done is satisfied.
