#!/usr/bin/env bash
set -euo pipefail

origin="${STAGING_PUBLIC_ORIGIN:?set STAGING_PUBLIC_ORIGIN}"

readarray -t parsed < <(python - "$origin" <<'PY'
from urllib.parse import urlparse
import sys

value = sys.argv[1]
parsed = urlparse(value)
if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
    raise SystemExit("STAGING_PUBLIC_ORIGIN must be a credential-free https origin")
if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
    raise SystemExit("STAGING_PUBLIC_ORIGIN must not contain a path, query, or fragment")
if parsed.port not in (None, 443):
    raise SystemExit("real staging must use standard HTTPS port 443")
print(parsed.hostname)
PY
)

host="${parsed[0]}"

headers="$(mktemp)"
trap 'rm -f "$headers"' EXIT

curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --proto '=https' \
  --tlsv1.2 \
  --max-time 15 \
  --dump-header "$headers" \
  --output /dev/null \
  "$origin/"

grep -Eiq '^strict-transport-security:[[:space:]]*max-age=' "$headers"
grep -Eiq '^x-content-type-options:[[:space:]]*nosniff' "$headers"
grep -Eiq '^x-frame-options:[[:space:]]*DENY' "$headers"

for port in 3000 8000 5432 6379; do
  if timeout 3 bash -c "</dev/tcp/$host/$port" >/dev/null 2>&1; then
    printf 'unexpected public TCP exposure on %s:%s\n' "$host" "$port" >&2
    exit 1
  fi
done

printf 'public staging TLS, headers, and port-isolation checks passed for %s\n' "$host"
