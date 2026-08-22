#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
tmp="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT

mkdir -p "$tmp/bin" "$tmp/home" "$tmp/backups"
log="$tmp/docker.log"

cat > "$tmp/bin/docker" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
: "${DEVFORGE_TEST_DOCKER_LOG:?}"
printf '%s|%s\n' "${DOCKER_CONFIG:-}" "$*" >> "$DEVFORGE_TEST_DOCKER_LOG"

if [ "${1:-}" = "login" ]; then
  cat >/dev/null
  exit 0
fi
if [ "${1:-}" = "logout" ]; then
  exit 0
fi
if [ "${1:-}" = "compose" ] && [[ " $* " == *" ps -q postgres "* ]]; then
  exit 0
fi
exit 0
MOCK
chmod +x "$tmp/bin/docker"

cat > "$tmp/bin/curl" <<'MOCK'
#!/usr/bin/env bash
exit 0
MOCK
chmod +x "$tmp/bin/curl"

printf 'postgres-test-secret\n' > "$tmp/postgres_password"
printf 'redis-test-secret\n' > "$tmp/redis_password"
chmod 0640 "$tmp/postgres_password" "$tmp/redis_password"

cat > "$tmp/release.env" <<EOF
STAGING_HOST=staging.example.com
STAGING_PUBLIC_ORIGIN=https://staging.example.com
STAGING_POSTGRES_PASSWORD_FILE=$tmp/postgres_password
STAGING_REDIS_PASSWORD_FILE=$tmp/redis_password
STAGING_BACKEND_IMAGE=ghcr.io/example/backend@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
STAGING_WEB_IMAGE=ghcr.io/example/web@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
STAGING_HTTP_BIND=80
STAGING_HTTPS_BIND=443
STAGING_CADDYFILE=./Caddyfile
STAGING_LOGIN_IP_LIMIT=10
EOF

export HOME="$tmp/home"
export PATH="$tmp/bin:$PATH"
export DEVFORGE_TEST_DOCKER_LOG="$log"
export DEVFORGE_STAGING_SECRET_GID="$(id -g)"

cd "$repo_root"
printf 'read-only-test-token' | bash infrastructure/staging/scripts/deploy-release.sh \
  "$tmp/release.env" \
  "$tmp/backups" \
  test-user

test -s "$log"

grep -q '|login ghcr.io -u test-user --password-stdin' "$log"
grep -q '|compose --env-file .* pull backend web' "$log"
grep -q '|compose --env-file .* up -d --no-build' "$log"
grep -q '|logout ghcr.io' "$log"

mapfile -t configs < <(cut -d'|' -f1 "$log" | grep -v '^$' | sort -u)
test "${#configs[@]}" -eq 1
registry_config="${configs[0]}"
[[ "$registry_config" == /tmp/* ]]
test ! -e "$registry_config"
test ! -e "$HOME/.docker/config.json"

printf 'staging deploy credential-isolation test passed\n'
