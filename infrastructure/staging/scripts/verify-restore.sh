#!/usr/bin/env bash
set -euo pipefail

backup_path="${1:?usage: verify-restore.sh <backup.dump>}"
test -s "$backup_path"

if [ -f "$backup_path.sha256" ]; then
  sha256sum -c "$backup_path.sha256"
fi

verify_db="devforge_restore_verify_$$"

cleanup() {
  docker compose -f infrastructure/staging/compose.yml exec -T postgres sh -ec "
    export PGPASSWORD=\"\$(cat /run/secrets/postgres_password)\"
    dropdb -h 127.0.0.1 -U devforge --if-exists '$verify_db'
  " >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose -f infrastructure/staging/compose.yml exec -T postgres sh -ec "
  export PGPASSWORD=\"\$(cat /run/secrets/postgres_password)\"
  createdb -h 127.0.0.1 -U devforge '$verify_db'
"

cat "$backup_path" | docker compose -f infrastructure/staging/compose.yml exec -T postgres sh -ec "
  export PGPASSWORD=\"\$(cat /run/secrets/postgres_password)\"
  pg_restore -h 127.0.0.1 -U devforge -d '$verify_db' --no-owner --no-privileges
"

schema_head="$(docker compose -f infrastructure/staging/compose.yml exec -T postgres sh -ec "
  export PGPASSWORD=\"\$(cat /run/secrets/postgres_password)\"
  psql -h 127.0.0.1 -U devforge -d '$verify_db' -Atqc 'SELECT version_num FROM alembic_version LIMIT 1'
")"

test -n "$schema_head"
printf 'restore verification passed at schema head %s\n' "$schema_head"
