#!/usr/bin/env bash
set -euo pipefail

origin="${STAGING_PUBLIC_ORIGIN:?set STAGING_PUBLIC_ORIGIN}"
[[ "$origin" == https://* ]]

if [ "${DEVFORGE_MONITOR_FORCE_FAILURE:-0}" = "1" ]; then
  drill_id="devforge-alert-drill-$(date -u +%Y%m%dT%H%M%SZ)"
  printf 'FORCED_MONITOR_FAILURE %s\n' "$drill_id" >&2
  printf 'This synthetic failure is intentional and must trigger the configured staging alert path.\n' >&2
  exit 42
fi

bash infrastructure/staging/scripts/verify-public-staging.sh
bash infrastructure/staging/scripts/healthcheck.sh
printf 'staging monitor probe passed for %s\n' "$origin"
