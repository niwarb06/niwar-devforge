#!/usr/bin/env bash
set -euo pipefail

release_dir="${1:?usage: write-release-metadata.sh <release-dir> <source-sha> <backend-image> <web-image> <workflow-run-id> [backup-reference]}"
source_sha="${2:?source SHA required}"
backend_image="${3:?backend image required}"
web_image="${4:?web image required}"
workflow_run_id="${5:?workflow run id required}"
backup_reference="${6:-}"

[[ "$release_dir" =~ ^/[A-Za-z0-9._/-]+$ ]]
[[ "$release_dir" != *"/../"* ]]
[[ "$release_dir" != *"/.." ]]
[[ "$source_sha" =~ ^[0-9a-f]{40}$ ]]
[[ "$backend_image" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]
[[ "$web_image" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]
[[ "$workflow_run_id" =~ ^[0-9]+$ ]]
test "$workflow_run_id" -gt 0

test -d "$release_dir"
test -f "$release_dir/release.env"

migration_head="$(
  cd "$release_dir"
  set -a
  # shellcheck disable=SC1091
  . ./release.env
  set +a
  docker compose --env-file release.env -f infrastructure/staging/compose.yml exec -T postgres sh -ec '
    export PGPASSWORD="$(cat /run/secrets/postgres_password)"
    psql -h 127.0.0.1 -U devforge -d devforge -Atqc "SELECT version_num FROM alembic_version LIMIT 1"
  '
)"
test -n "$migration_head"

completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
output="$release_dir/release-metadata.json"
tmp="$output.tmp"

SOURCE_SHA="$source_sha" \
BACKEND_IMAGE="$backend_image" \
WEB_IMAGE="$web_image" \
WORKFLOW_RUN_ID="$workflow_run_id" \
MIGRATION_HEAD="$migration_head" \
COMPLETED_AT="$completed_at" \
BACKUP_REFERENCE="$backup_reference" \
python3 - "$tmp" <<'PY'
import json, os, sys
payload = {
    "schema_version": 1,
    "source_sha": os.environ["SOURCE_SHA"],
    "backend_image": os.environ["BACKEND_IMAGE"],
    "web_image": os.environ["WEB_IMAGE"],
    "workflow_run_id": int(os.environ["WORKFLOW_RUN_ID"]),
    "migration_head": os.environ["MIGRATION_HEAD"],
    "deployed_at": os.environ["COMPLETED_AT"],
    "backup_reference": os.environ["BACKUP_REFERENCE"] or None,
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
chmod 0600 "$tmp"
mv "$tmp" "$output"
printf '%s\n' "$output"
