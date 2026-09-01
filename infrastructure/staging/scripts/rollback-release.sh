#!/usr/bin/env bash
set -euo pipefail

previous_env="${1:?usage: rollback-release.sh <previous-release.env> <previous-release.meta.json> <backup-dir> <registry-user>}"
previous_meta="${2:?usage: rollback-release.sh <previous-release.env> <previous-release.meta.json> <backup-dir> <registry-user>}"
backup_dir="${3:?usage: rollback-release.sh <previous-release.env> <previous-release.meta.json> <backup-dir> <registry-user>}"
registry_user="${4:?usage: rollback-release.sh <previous-release.env> <previous-release.meta.json> <backup-dir> <registry-user>}"

for file in "$previous_env" "$previous_meta"; do
  test -f "$file"
done
[[ "$backup_dir" =~ ^/[A-Za-z0-9._/-]+$ ]]
[[ "$backup_dir" != *"/../"* ]]
[[ "$backup_dir" != *"/.." ]]
[[ "$registry_user" =~ ^[A-Za-z0-9._-]+$ ]]

python3 infrastructure/staging/scripts/release_guard.py validate --path "$previous_meta"

# The fixed Compose project name lets the current toolset inspect the running staging
# database even while using the previous release's environment values for secrets.
current_schema_head="$(
  docker compose \
    --env-file "$previous_env" \
    -f infrastructure/staging/compose.yml \
    exec -T postgres sh -ec '
      export PGPASSWORD="$(cat /run/secrets/postgres_password)"
      psql -h 127.0.0.1 -U devforge -d devforge -Atqc "SELECT version_num FROM alembic_version LIMIT 1"
    '
)"

test -n "$current_schema_head"
python3 infrastructure/staging/scripts/release_guard.py \
  assert-schema-compatible \
  --path "$previous_meta" \
  --current-schema-head "$current_schema_head"

# deploy-release.sh consumes the read-only registry token from stdin, takes a fresh
# pre-change backup, uses an ephemeral Docker auth directory, and runs health checks.
# This rollback intentionally changes only application image digests. Infrastructure
# or schema rollback requires a separate reviewed plan.
exec bash infrastructure/staging/scripts/deploy-release.sh \
  "$previous_env" \
  "$backup_dir" \
  "$registry_user"
