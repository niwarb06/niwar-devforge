#!/usr/bin/env python3
"""Provider-neutral staging monitor with fail-closed HTTPS and transition alerts."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


USER_AGENT = "Niwar-DevForge-Staging-Monitor/1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_loopback(hostname: str | None) -> bool:
    return hostname in {"127.0.0.1", "localhost", "::1"}


def validate_url(url: str, *, allow_loopback_http: bool = False) -> str:
    parsed = urlsplit(url)
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")
    if parsed.query or parsed.fragment:
        raise ValueError("monitor URLs must not include query strings or fragments")
    if parsed.scheme == "https" and parsed.hostname:
        return url.rstrip("/")
    if (
        allow_loopback_http
        and parsed.scheme == "http"
        and _is_loopback(parsed.hostname)
    ):
        return url.rstrip("/")
    raise ValueError("URL must use HTTPS; HTTP is allowed only for explicit loopback tests")


def _request(url: str, *, timeout: float, expected_statuses: set[int]) -> tuple[bool, str]:
    request = Request(url, headers={"user-agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            status = int(response.status)
    except HTTPError as exc:
        status = int(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        return False, f"request_error:{type(exc).__name__}"
    if status not in expected_statuses:
        return False, f"unexpected_status:{status}"
    return True, f"status:{status}"


def probe_origin(origin: str, *, timeout: float = 10.0) -> tuple[bool, str]:
    public_ok, public_reason = _request(
        urljoin(origin + "/", "/"),
        timeout=timeout,
        expected_statuses={200},
    )
    if not public_ok:
        return False, f"public:{public_reason}"

    auth_ok, auth_reason = _request(
        urljoin(origin + "/", "/api/auth/me"),
        timeout=timeout,
        expected_statuses={200, 401},
    )
    if not auth_ok:
        return False, f"auth_path:{auth_reason}"
    return True, f"public:{public_reason};auth_path:{auth_reason}"


def _safe_reason(reason: str) -> str:
    return reason.replace("\n", " ").replace("\r", " ")[:240]


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "unknown"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "unknown"}
    return data if isinstance(data, dict) else {"status": "unknown"}


def write_private_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def append_event(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    finally:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def send_webhook(
    webhook_url: str,
    payload: dict[str, object],
    *,
    bearer_token: str | None = None,
    timeout: float = 10.0,
    allow_loopback_http: bool = False,
) -> None:
    target = validate_url(webhook_url, allow_loopback_http=allow_loopback_http)
    headers = {
        "content-type": "application/json",
        "user-agent": USER_AGENT,
    }
    if bearer_token:
        headers["authorization"] = f"Bearer {bearer_token}"
    request = Request(
        target,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            status = int(response.status)
    except HTTPError as exc:
        status = int(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"alert delivery failed: {type(exc).__name__}") from exc
    if status < 200 or status >= 300:
        raise RuntimeError(f"alert delivery failed with HTTP {status}")


@dataclass(frozen=True)
class MonitorConfig:
    origin: str
    state_file: Path
    event_log: Path
    webhook_url: str | None = None
    bearer_token: str | None = None
    timeout: float = 10.0
    allow_loopback_http: bool = False


def run_once(
    config: MonitorConfig,
    *,
    probe: Callable[[str], tuple[bool, str]] | None = None,
) -> bool:
    origin = validate_url(config.origin, allow_loopback_http=config.allow_loopback_http)
    probe_fn = probe or (lambda value: probe_origin(value, timeout=config.timeout))
    healthy, reason = probe_fn(origin)
    status = "healthy" if healthy else "unhealthy"
    previous = load_state(config.state_file)
    previous_status = str(previous.get("status", "unknown"))
    now = utc_now()

    event = {
        "schema_version": 1,
        "timestamp": now,
        "service": "web-staging",
        "origin": origin,
        "status": status,
        "previous_status": previous_status,
        "reason": _safe_reason(reason),
    }
    append_event(config.event_log, event)

    should_alert = (
        (status == "unhealthy" and previous_status != "unhealthy")
        or (status == "healthy" and previous_status == "unhealthy")
    )
    if should_alert and config.webhook_url:
        alert = {
            "schema_version": 1,
            "event": "staging_health_transition",
            "service": "web-staging",
            "origin": origin,
            "state": "resolved" if healthy else "firing",
            "observed_status": status,
            "previous_status": previous_status,
            "reason": _safe_reason(reason),
            "timestamp": now,
        }
        send_webhook(
            config.webhook_url,
            alert,
            bearer_token=config.bearer_token,
            timeout=config.timeout,
            allow_loopback_http=config.allow_loopback_http,
        )

    write_private_json(
        config.state_file,
        {
            "schema_version": 1,
            "status": status,
            "reason": _safe_reason(reason),
            "checked_at": now,
            "last_change_at": now if status != previous_status else previous.get("last_change_at", now),
        },
    )
    return healthy


def send_drill(config: MonitorConfig) -> None:
    if not config.webhook_url:
        raise RuntimeError("STAGING_ALERT_WEBHOOK_URL is required for an alert drill")
    origin = validate_url(config.origin, allow_loopback_http=config.allow_loopback_http)
    send_webhook(
        config.webhook_url,
        {
            "schema_version": 1,
            "event": "staging_alert_delivery_drill",
            "service": "web-staging",
            "origin": origin,
            "state": "test",
            "timestamp": utc_now(),
        },
        bearer_token=config.bearer_token,
        timeout=config.timeout,
        allow_loopback_http=config.allow_loopback_http,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument("--event-log", required=True, type=Path)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--alert-drill", action="store_true")
    parser.add_argument("--allow-insecure-loopback", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.interval_seconds < 15:
        raise SystemExit("interval must be at least 15 seconds")
    config = MonitorConfig(
        origin=args.origin,
        state_file=args.state_file,
        event_log=args.event_log,
        webhook_url=os.environ.get("STAGING_ALERT_WEBHOOK_URL"),
        bearer_token=os.environ.get("STAGING_ALERT_WEBHOOK_BEARER") or None,
        timeout=args.timeout_seconds,
        allow_loopback_http=args.allow_insecure_loopback,
    )
    if args.alert_drill:
        send_drill(config)
        print("staging alert delivery drill passed")
        return 0
    if args.once:
        return 0 if run_once(config) else 2

    while True:
        try:
            run_once(config)
        except Exception as exc:  # bounded daemon error; never print secrets or response bodies
            print(f"monitor iteration failed: {type(exc).__name__}: {_safe_reason(str(exc))}", file=sys.stderr)
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
