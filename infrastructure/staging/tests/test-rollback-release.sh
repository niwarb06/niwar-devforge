#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

current="$tmp/current"
previous="$tmp/previous"
backup_dir="$tmp/backups"
mock_bin="$tmp/bin"
mkdir -p "$current" "$previous" "$backup_dir" "$mock_bin"

for release in "$current" "$previous"; do
  mkdir -p "$release/infrastructure/staging"
  ln -s "$repo_root/infrastructure/staging/scripts" "$release/infrastructure/staging/scripts"
  ln -s "$repo_root/infrastructure/staging/compose.yml" "$release/infrastructure/staging/compose.yml"
done

cat > "$current/release.env" <<'EOF'
STAGING_HOST=staging.example.invalid
STAGING_PUBLIC_ORIGIN=https://staging.example.invalid
STAGING_POSTGRES_PASSWORD_FILE=/tmp/postgres_password
STAGING_REDIS_PASSWORD_FILE=/tmp/redis_password
STAGING_BACKEND_IMAGE=ghcr.io/niwarb06/niwar-devforge/backend-staging@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
STAGING_WEB_IMAGE=ghcr.io/niwarb06/niwar-devforge/web-staging@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
EOF

cat > "$previous/release.env" <<'EOF'
STAGING_HOST=staging.example.invalid
STAGING_PUBLIC_ORIGIN=https://staging.example.invalid
STAGING_POSTGRES_PASSWORD_FILE=/tmp/postgres_password
STAGING_REDIS_PASSWORD_FILE=/tmp/redis_password
STAGING_BACKEND_IMAGE=ghcr.io/niwarb06/niwar-devforge/backend-staging@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
STAGING_WEB_IMAGE=ghcr.io/niwarb06/niwar-devforge/web-staging@sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
EOF

cat > "$previous/release-metadata.json" <<'EOF'
{
  "migration_head": "abc123"
}
EOF

cat > "$mock_bin/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
args="$*"
if [[ "$args" == *"alembic_version"* ]]; then
  printf 'abc123\n'
elif [[ "$args" == *"pg_dump"* ]]; then
  printf 'mock-postgres-dump\n'
elif [[ "$args" == *" redis "* || "$args" == *" redis" ]]; then
  printf 'PONG\n'
fi
exit 0
EOF
chmod +x "$mock_bin/docker"

cat > "$mock_bin/curl" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$mock_bin/curl"

PATH="$mock_bin:$PATH" STAGING_PUBLIC_ORIGIN=https://staging.example.invalid \
  bash "$repo_root/infrastructure/staging/scripts/rollback-release.sh" \
  "$current" "$previous" "$backup_dir" ROLLBACK-STAGING \
  > "$tmp/success.log"

grep -q 'staging app rollback completed without schema downgrade' "$tmp/success.log"
grep -q 'migration_head=abc123' "$tmp/success.log"
find "$backup_dir" -type f -name '*.dump' -size +0c | grep -q .
find "$backup_dir" -type f -name '*.dump.sha256' -size +0c | grep -q .

python3 - "$previous/release-metadata.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
data["migration_head"] = "different-head"
open(path, "w", encoding="utf-8").write(json.dumps(data))
PY

if PATH="$mock_bin:$PATH" STAGING_PUBLIC_ORIGIN=https://staging.example.invalid \
  bash "$repo_root/infrastructure/staging/scripts/rollback-release.sh" \
  "$current" "$previous" "$backup_dir" ROLLBACK-STAGING \
  > "$tmp/mismatch.log" 2>&1; then
  echo 'rollback unexpectedly allowed schema mismatch' >&2
  exit 1
fi
grep -q 'rollback blocked: current schema head abc123 differs from previous release head different-head' "$tmp/mismatch.log"

if PATH="$mock_bin:$PATH" STAGING_PUBLIC_ORIGIN=https://staging.example.invalid \
  bash "$repo_root/infrastructure/staging/scripts/rollback-release.sh" \
  "$current" "$previous" "$backup_dir" WRONG-CONFIRMATION \
  >/dev/null 2>&1; then
  echo 'rollback unexpectedly accepted wrong confirmation' >&2
  exit 1
fi

printf 'staging rollback control-plane proof passed\n'
