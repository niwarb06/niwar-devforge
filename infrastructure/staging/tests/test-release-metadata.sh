#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
release="$tmp/release"
mock_bin="$tmp/bin"
mkdir -p "$release/infrastructure/staging" "$mock_bin"
ln -s "$repo_root/infrastructure/staging/compose.yml" "$release/infrastructure/staging/compose.yml"

cat > "$release/release.env" <<'EOF'
STAGING_HOST=staging.example.invalid
STAGING_PUBLIC_ORIGIN=https://staging.example.invalid
STAGING_POSTGRES_PASSWORD_FILE=/tmp/postgres_password
STAGING_REDIS_PASSWORD_FILE=/tmp/redis_password
STAGING_BACKEND_IMAGE=ghcr.io/niwarb06/niwar-devforge/backend-staging@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
STAGING_WEB_IMAGE=ghcr.io/niwarb06/niwar-devforge/web-staging@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
EOF

cat > "$mock_bin/docker" <<'EOF'
#!/usr/bin/env bash
printf '20260822190000_release_candidate\n'
EOF
chmod +x "$mock_bin/docker"

source_sha="0123456789abcdef0123456789abcdef01234567"
backend="ghcr.io/niwarb06/niwar-devforge/backend-staging@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
web="ghcr.io/niwarb06/niwar-devforge/web-staging@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

PATH="$mock_bin:$PATH" bash "$repo_root/infrastructure/staging/scripts/write-release-metadata.sh" \
  "$release" "$source_sha" "$backend" "$web" 123456 "$tmp/predeploy.dump.sha256" >/dev/null

python3 - "$release/release-metadata.json" <<'PY'
import json, re, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)
assert data["schema_version"] == 1
assert data["source_sha"] == "0123456789abcdef0123456789abcdef01234567"
assert data["workflow_run_id"] == 123456
assert data["migration_head"] == "20260822190000_release_candidate"
assert data["backend_image"].startswith("ghcr.io/") and "@sha256:" in data["backend_image"]
assert data["web_image"].startswith("ghcr.io/") and "@sha256:" in data["web_image"]
assert data["backup_reference"].endswith("predeploy.dump.sha256")
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", data["deployed_at"])
PY

mode="$(stat -c '%a' "$release/release-metadata.json")"
test "$mode" = "600"
printf 'staging release metadata proof passed\n'
