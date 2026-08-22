#!/usr/bin/env bash
set -euo pipefail

release_env="${1:-release.env}"
backup_dir="${2:?usage: deploy-release.sh <release.env> <backup-dir> <registry-user>}"
registry_user="${3:?usage: deploy-release.sh <release.env> <backup-dir> <registry-user>}"

test -f "$release_env"
[[ "$backup_dir" =~ ^/[A-Za-z0-9._/-]+$ ]]
[[ ! "$backup_dir" =~ (^|/)\.\.($|/) ]]
[[ "$registry_user" =~ ^[A-Za-z0-9._-]+$ ]]

set -a
# shellcheck disable=SC1090
. "$release_env"
set +a

bash infrastructure/staging/scripts/validate-host-secrets.sh

registry_config="$(mktemp -d)"
chmod 0700 "$registry_config"
cleanup() {
  rm -rf "$registry_config"
}
trap cleanup EXIT
export DOCKER_CONFIG="$registry_config"

docker login ghcr.io -u "$registry_user" --password-stdin >/dev/null

mkdir -p "$backup_dir"
if docker compose --env-file "$release_env" -f infrastructure/staging/compose.yml ps -q postgres | grep -q .; then
  bash infrastructure/staging/scripts/backup.sh "$backup_dir"
fi

docker compose --env-file "$release_env" -f infrastructure/staging/compose.yml pull backend web
docker compose --env-file "$release_env" -f infrastructure/staging/compose.yml up -d --no-build

healthy=0
for attempt in $(seq 1 60); do
  if bash infrastructure/staging/scripts/healthcheck.sh; then
    healthy=1
    break
  fi
  sleep 2
done

if [ "$healthy" != "1" ]; then
  docker compose --env-file "$release_env" -f infrastructure/staging/compose.yml ps >&2 || true
  docker compose --env-file "$release_env" -f infrastructure/staging/compose.yml logs --no-color --tail=200 >&2 || true
  printf 'staging did not become healthy after deployment\n' >&2
  exit 1
fi

docker logout ghcr.io >/dev/null 2>&1 || true
cleanup
trap - EXIT
