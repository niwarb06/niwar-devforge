#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "release_guard.py"
spec = importlib.util.spec_from_file_location("release_guard", MODULE_PATH)
assert spec and spec.loader
release_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_guard)


VALID = {
    "schema_version": 1,
    "source_sha": "a" * 40,
    "backend_image": "ghcr.io/niwarb06/niwar-devforge/backend-staging@sha256:" + "b" * 64,
    "web_image": "ghcr.io/niwarb06/niwar-devforge/web-staging@sha256:" + "c" * 64,
    "database_schema_head": "20260822190000_auth",
    "workflow_run_id": 123456,
    "deployed_at": "2026-08-22T20:00:00Z",
}


class ReleaseGuardTests(unittest.TestCase):
    def test_valid_payload_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.meta.json"
            release_guard.write(path, dict(VALID))
            loaded = release_guard.load(path)
            self.assertEqual(loaded, VALID)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_mutable_image_reference_is_rejected(self) -> None:
        payload = dict(VALID)
        payload["backend_image"] = "ghcr.io/niwarb06/niwar-devforge/backend-staging:latest"
        with self.assertRaises(ValueError):
            release_guard.validate_payload(payload)

    def test_extra_keys_are_rejected(self) -> None:
        payload = dict(VALID)
        payload["operator_note"] = "unexpected"
        with self.assertRaises(ValueError):
            release_guard.validate_payload(payload)

    def test_invalid_source_sha_is_rejected(self) -> None:
        payload = dict(VALID)
        payload["source_sha"] = "not-a-sha"
        with self.assertRaises(ValueError):
            release_guard.validate_payload(payload)

    def test_corrupt_json_is_rejected_without_echoing_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.meta.json"
            path.write_text('{"secret":"value",', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unable to load release metadata") as caught:
                release_guard.load(path)
            self.assertNotIn("secret", str(caught.exception))
            self.assertNotIn("value", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
