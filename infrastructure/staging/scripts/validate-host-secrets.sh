#!/usr/bin/env bash
set -euo pipefail

postgres_secret="${STAGING_POSTGRES_PASSWORD_FILE:?set STAGING_POSTGRES_PASSWORD_FILE}"
redis_secret="${STAGING_REDIS_PASSWORD_FILE:?set STAGING_REDIS_PASSWORD_FILE}"
expected_gid="${DEVFORGE_STAGING_SECRET_GID:-10001}"

validate_secret() {
  local path="$1"
  local label="$2"

  test -f "$path"
  test ! -L "$path"
  test -s "$path"

  local mode gid
  mode="$(stat -c '%a' "$path")"
  gid="$(stat -c '%g' "$path")"

  if [ "$mode" != "640" ]; then
    printf '%s secret must use mode 0640; found %s\n' "$label" "$mode" >&2
    exit 1
  fi

  if [ "$gid" != "$expected_gid" ]; then
    printf '%s secret must use group %s; found %s\n' "$label" "$expected_gid" "$gid" >&2
    exit 1
  fi
}

validate_secret "$postgres_secret" postgres
validate_secret "$redis_secret" redis

printf 'staging host secret metadata passed\n'
