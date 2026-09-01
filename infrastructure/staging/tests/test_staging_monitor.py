#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "observability" / "staging_monitor.py"
spec = importlib.util.spec_from_file_location("staging_monitor", MODULE_PATH)
assert spec and spec.loader
monitor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = monitor
spec.loader.exec_module(monitor)


class _SinkHandler(BaseHTTPRequestHandler):
    payloads: list[dict[str, object]] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length)
        self.__class__.payloads.append(json.loads(body))
        self.send_response(204)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


class StagingMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        _SinkHandler.payloads = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _SinkHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.config = monitor.MonitorConfig(
            origin="http://127.0.0.1:8080",
            state_file=root / "state.json",
            event_log=root / "events.jsonl",
            webhook_url=f"http://127.0.0.1:{self.server.server_port}/alert",
            allow_loopback_http=True,
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_initial_healthy_state_is_quiet(self) -> None:
        self.assertTrue(
            monitor.run_once(self.config, probe=lambda _origin: (True, "status:200"))
        )
        self.assertEqual(_SinkHandler.payloads, [])
        state = json.loads(self.config.state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "healthy")

    def test_failure_deduplicates_and_recovery_resolves(self) -> None:
        self.assertFalse(
            monitor.run_once(self.config, probe=lambda _origin: (False, "status:503"))
        )
        self.assertEqual(len(_SinkHandler.payloads), 1)
        self.assertEqual(_SinkHandler.payloads[0]["state"], "firing")

        self.assertFalse(
            monitor.run_once(self.config, probe=lambda _origin: (False, "status:503"))
        )
        self.assertEqual(len(_SinkHandler.payloads), 1, "repeat failure must not spam alerts")

        self.assertTrue(
            monitor.run_once(self.config, probe=lambda _origin: (True, "status:200"))
        )
        self.assertEqual(len(_SinkHandler.payloads), 2)
        self.assertEqual(_SinkHandler.payloads[1]["state"], "resolved")

        state = json.loads(self.config.state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "healthy")
        events = self.config.event_log.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(events), 3)

    def test_alert_delivery_drill(self) -> None:
        monitor.send_drill(self.config)
        self.assertEqual(len(_SinkHandler.payloads), 1)
        self.assertEqual(_SinkHandler.payloads[0]["event"], "staging_alert_delivery_drill")
        self.assertEqual(_SinkHandler.payloads[0]["state"], "test")

    def test_http_is_rejected_outside_explicit_loopback_mode(self) -> None:
        with self.assertRaises(ValueError):
            monitor.validate_url("http://example.com")
        with self.assertRaises(ValueError):
            monitor.validate_url("http://127.0.0.1:9000")
        self.assertEqual(
            monitor.validate_url("http://127.0.0.1:9000", allow_loopback_http=True),
            "http://127.0.0.1:9000",
        )

    def test_embedded_credentials_and_query_strings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            monitor.validate_url("https://user:password@example.com")
        with self.assertRaises(ValueError):
            monitor.validate_url("https://example.com/?token=secret")


if __name__ == "__main__":
    unittest.main()
