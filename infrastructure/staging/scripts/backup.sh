#!/usr/bin/env bash
set -euo pipefail

backup_dir="${1:-./.staging-backups}"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="$backup_dir/devforge-staging-$timestamp.dump"
tmp_path="$backup_path.tmp"

cleanup() {
  rm -f "$tmp_path"
}
trap cleanup EXIT

docker compose -f infrastructure/staging/compose.yml exec -T postgres sh -ec '
  export PGPASSWORD="$(cat /run/secrets/postgres_password)"
  exec pg_dump -h 127.0.0.1 -U devforge -d devforge -Fc
' > "$tmp_path"

test -s "$tmp_path"
chmod 600 "$tmp_path"
mv "$tmp_path" "$backup_path"
sha256sum "$backup_path" > "$backup_path.sha256"
chmod 600 "$backup_path.sha256"

trap - EXIT
printf '%s\n' "$backup_path"
