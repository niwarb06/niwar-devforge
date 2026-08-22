#!/usr/bin/env bash
set -euo pipefail

current_release_dir="${1:?usage: rollback-release.sh <current-release-dir> <previous-release-dir> <backup-dir> ROLLBACK-STAGING}"
previous_release_dir="${2:?usage: rollback-release.sh <current-release-dir> <previous-release-dir> <backup-dir> ROLLBACK-STAGING}"
backup_dir="${3:?usage: rollback-release.sh <current-release-dir> <previous-release-dir> <backup-dir> ROLLBACK-STAGING}"
confirm="${4:?usage: rollback-release.sh <current-release-dir> <previous-release-dir> <backup-dir> ROLLBACK-STAGING}"

test "$confirm" = "ROLLBACK-STAGING"

for path in "$current_release_dir" "$previous_release_dir" "$backup_dir"; do
  [[ "$path" =~ ^/[A-Za-z0-9._/-]+$ ]]
  [[ "$path" != *"/../"* ]]
  [[ "$path" != *"/.." ]]
done

test "$current_release_dir" != "$previous_release_dir"
test -f "$current_release_dir/release.env"
test -f "$previous_release_dir/release.env"
test -f "$previous_release_dir/release-metadata.json"

read_env_value() {
  local file="$1"
  local key="$2"
  local value
  value="$(sed -n "s/^${key}=//p" "$file")"
  test -n "$value"
  printf '%s' "$value"
}

previous_backend="$(read_env_value "$previous_release_dir/release.env" STAGING_BACKEND_IMAGE)"
previous_web="$(read_env_value "$previous_release_dir/release.env" STAGING_WEB_IMAGE)"
[[ "$previous_backend" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]
[[ "$previous_web" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]

previous_schema_head="$(python3 - "$previous_release_dir/release-metadata.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
value = data.get("migration_head")
if not isinstance(value, str) or not value.strip():
    raise SystemExit("previous release metadata lacks migration_head")
print(value)
PY
)"

current_schema_head="$(
  cd "$current_release_dir"
  set -a
  # shellcheck disable=SC1091
  . ./release.env
  set +a
  docker compose --env-file release.env -f infrastructure/staging/compose.yml exec -T postgres sh -ec '
    export PGPASSWORD="$(cat /run/secrets/postgres_password)"
    psql -h 127.0.0.1 -U devforge -d devforge -Atqc "SELECT version_num FROM alembic_version LIMIT 1"
  '
)"

test -n "$current_schema_head"
if [ "$current_schema_head" != "$previous_schema_head" ]; then
  printf 'rollback blocked: current schema head %s differs from previous release head %s\n' \
    "$current_schema_head" "$previous_schema_head" >&2
  printf 'A migration-specific reviewed recovery plan is required; this script never downgrades schema.\n' >&2
  exit 1
fi

backup_path="$(
  cd "$current_release_dir"
  set -a
  # shellcheck disable=SC1091
  . ./release.env
  set +a
  bash infrastructure/staging/scripts/backup.sh "$backup_dir"
)"
test -s "$backup_path"
test -s "$backup_path.sha256"

(
  cd "$previous_release_dir"
  set -a
  # shellcheck disable=SC1091
  . ./release.env
  set +a
  docker compose --env-file release.env -f infrastructure/staging/compose.yml pull backend web
  docker compose --env-file release.env -f infrastructure/staging/compose.yml up -d --no-build

  for attempt in $(seq 1 30); do
    if bash infrastructure/staging/scripts/healthcheck.sh; then
      printf 'rollback health validation passed on attempt %s\n' "$attempt"
      break
    fi
    if [ "$attempt" -eq 30 ]; then
      echo 'rollback health validation failed' >&2
      docker compose --env-file release.env -f infrastructure/staging/compose.yml ps >&2 || true
      exit 1
    fi
    sleep 2
  done
)

printf 'staging app rollback completed without schema downgrade\n'
printf 'previous_release=%s\n' "$previous_release_dir"
printf 'migration_head=%s\n' "$previous_schema_head"
printf 'pre_rollback_backup=%s\n' "$backup_path"
