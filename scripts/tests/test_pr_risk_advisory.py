"""Tests for the conservative advisory classifier."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pr_risk_advisory import HIGH, LOW, MEDIUM, classify_changes, classify_path, git_changes


class PrRiskAdvisoryTests(unittest.TestCase):
    def test_plain_docs_and_test_only_are_low(self):
        self.assertEqual(classify_path("docs/13_PILOT_PROOF_METRICS.md")[0], LOW)
        self.assertEqual(classify_path("generator/tests/phase5-roadmap-acceptance.test.mjs")[0], LOW)

    def test_workflows_source_and_unknown_are_medium(self):
        for path in ("generator/generate.mjs", "package.json", "unknown.bin",
                     ".github/workflows/generator-flutter-auth-ci.yml"):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path)[0], MEDIUM)

    def test_protected_and_sensitive_are_high(self):
        for path in ("AGENTS.md", ".github/workflows/required-pr-gate.yml",
                     ".github/rulesets/protect-main.json", "docs/07_AI_AGENT_RULES.md",
                     "docs/21_PR_RISK_AND_REVIEW_POLICY.md",
                     "scripts/pr_risk_advisory.py", "scripts/tests/test_pr_risk_advisory.py",
                     "packages/backend-core/migrations/0001.py",
                     "packages/payments/MODULE.md",
                     "packages/flutter-auth-core/lib/session.dart",
                     "infrastructure/staging/config.yml"):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path)[0], HIGH)

    def test_sensitive_test_and_doc_filenames_do_not_auto_merge(self):
        for path in (
            "generator/tests/generated-database-migrations.test.mjs",
            "generator/tests/generated-backend-alembic.test.mjs",
            "generator/tests/generated-flutter-auth.test.mjs",
            "apps/web_next/tests/e2e/auth.spec.ts",
            "docs/security-hardening.md",
            "tests/permissions.test.ts",
            "generator/tests/generated-payment-contract.test.mjs",
        ):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path)[0], HIGH)

    def test_ci_test_files_require_review(self):
        for path in (
            "generator/tests/flutter-ci-recovery-contract.test.mjs",
            "generator/tests/generated-ci.test.mjs",
            "docs/ci-runner-guidance.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path)[0], MEDIUM)
        self.assertEqual(classify_path("docs/authors-guide.md")[0], LOW)
        self.assertEqual(classify_path("generator/tests/generator.test.mjs")[0], LOW)

    def test_deletions_never_low(self):
        self.assertEqual(classify_path("docs/README.md", "D")[0], MEDIUM)

    def test_unknown_operations_and_noncanonical_paths_fail_closed(self):
        for path in ("../AGENTS.md", "docs/../README.md", "/etc/passwd",
                     r"docs\file.md", "", "./README.md", "docs//a.md", "docs/a\n.md"):
            with self.subTest(path=path):
                self.assertEqual(classify_path(path)[0], HIGH)
        self.assertEqual(classify_path("README.md", "R100")[0], HIGH)

    def test_highest_risk_wins_and_empty_is_high(self):
        values = [("M", "README.md"), ("A", "generator/generate.mjs"),
                  ("M", "AGENTS.md")]
        self.assertEqual(classify_changes(values)["level"], "HIGH")
        self.assertEqual(classify_changes(list(reversed(values)))["level"], "HIGH")
        self.assertEqual(classify_changes([])["level"], "HIGH")

    def test_git_diff_uses_nul_separators(self):
        fake = SimpleNamespace(stdout=b"M\0docs/README.md\0A\0generator/tests/new.test.mjs\0")
        with patch("pr_risk_advisory.subprocess.run", return_value=fake) as run:
            changes = git_changes("0" * 40)
        self.assertEqual(changes, [("M", "docs/README.md"),
                                   ("A", "generator/tests/new.test.mjs")])
        self.assertIn("--no-renames", run.call_args.args[0])

    def test_base_sha_injection_is_rejected(self):
        with self.assertRaises(ValueError):
            git_changes("HEAD; echo unsafe")


if __name__ == "__main__":
    unittest.main()
