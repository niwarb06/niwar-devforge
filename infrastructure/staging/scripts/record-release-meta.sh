#!/usr/bin/env bash
set -euo pipefail

release_env="${1:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"
meta_path="${2:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"
source_sha="${3:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"
backend_image="${4:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"
web_image="${5:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"
workflow_run_id="${6:?usage: record-release-meta.sh <release.env> <release.meta.json> <source-sha> <backend-image> <web-image> <workflow-run-id>}"

test -f "$release_env"

schema_head="$(
  docker compose \
    --env-file "$release_env" \
    -f infrastructure/staging/compose.yml \
    exec -T postgres sh -ec '
      export PGPASSWORD="$(cat /run/secrets/postgres_password)"
      psql -h 127.0.0.1 -U devforge -d devforge -Atqc "SELECT version_num FROM alembic_version LIMIT 1"
    '
)"

test -n "$schema_head"
python3 infrastructure/staging/scripts/release_guard.py record \
  --path "$meta_path" \
  --source-sha "$source_sha" \
  --backend-image "$backend_image" \
  --web-image "$web_image" \
  --database-schema-head "$schema_head" \
  --workflow-run-id "$workflow_run_id"
