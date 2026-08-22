#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

set +e
STAGING_PUBLIC_ORIGIN=https://staging.example.invalid \
DEVFORGE_MONITOR_FORCE_FAILURE=1 \
  bash "$repo_root/infrastructure/staging/scripts/monitor-staging.sh" \
  >"$tmp/stdout.log" 2>"$tmp/stderr.log"
status=$?
set -e

test "$status" -eq 42
grep -Eq '^FORCED_MONITOR_FAILURE devforge-alert-drill-[0-9]{8}T[0-9]{6}Z$' "$tmp/stderr.log"
grep -q 'synthetic failure is intentional' "$tmp/stderr.log"
printf 'staging monitoring synthetic-failure proof passed\n'
