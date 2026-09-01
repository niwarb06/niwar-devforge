#!/usr/bin/env bash
set -euo pipefail

origin="${STAGING_PUBLIC_ORIGIN:?set STAGING_PUBLIC_ORIGIN}"

curl_args=(--fail --silent --show-error --max-time 10)
if [ "${STAGING_ALLOW_INTERNAL_CA:-0}" = "1" ]; then
  curl_args+=(--insecure)
fi

curl "${curl_args[@]}" "$origin/" >/dev/null

docker compose -f infrastructure/staging/compose.yml exec -T backend \
  python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).read()"

docker compose -f infrastructure/staging/compose.yml exec -T postgres \
  pg_isready -U devforge -d devforge >/dev/null

docker compose -f infrastructure/staging/compose.yml exec -T redis sh -ec \
  'REDISCLI_AUTH="$(cat /run/secrets/redis_password)" redis-cli ping | grep -q PONG'

printf 'staging health checks passed\n'
