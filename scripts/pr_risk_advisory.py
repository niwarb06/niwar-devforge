"""Conservative advisory PR path classification, not a GitHub merge gate."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import PurePosixPath

LOW, MEDIUM, HIGH = range(3)
LEVELS = ("LOW", "MEDIUM", "HIGH")
PROTECTED = frozenset({
    "AGENTS.md", "SECURITY.md", ".github/CODEOWNERS",
    ".gitleaks.toml", ".gitleaksignore",
    ".github/workflows/required-pr-gate.yml",
    "docs/03_OSS_INTAKE_POLICY.md", "docs/04_SECURITY_BASELINE.md",
    "docs/07_AI_AGENT_RULES.md", "docs/09_QUALITY_GATES.md",
    "docs/12_DEFINITION_OF_DONE.md",
    "docs/21_PR_RISK_AND_REVIEW_POLICY.md",
    "scripts/pr_risk_advisory.py", "scripts/tests/test_pr_risk_advisory.py",
})
SENSITIVE = frozenset({
    "auth", "authentication", "authorization", "rbac", "permissions",
    "identity", "verification", "kyc", "payments", "payment",
    "wallet", "wallet-ledger", "secrets", "credentials",
    "migrations", "production", "staging", "release",
    "flutter-auth-core", "web-session-core", "web-bff-core",
})

def classify_path(path: str, status: str = "M") -> tuple[int, str]:
    """Fail closed on unknown operations or untrusted paths."""
    if not isinstance(path, str) or not path or "\\" in path:
        return HIGH, "invalid path"
    if path.startswith("/") or any(p in ("", ".", "..") for p in path.split("/")):
        return HIGH, "non-canonical path"
    if any(ord(c) < 32 or ord(c) == 127 for c in path):
        return HIGH, "control character in path"
    if status not in ("A", "M", "D"):
        return HIGH, "unsupported git change status"
    if path in PROTECTED or path.startswith(".github/rulesets/"):
        return HIGH, "protected governance or merge control"
    parts = PurePosixPath(path).parts
    # Security/CI intent can appear in a filename, not just in a directory.
    # For example generated-database-migrations.test.mjs must never be LOW.
    tokens = {token for part in parts for token in re.split(r"[-_.]", part.lower())}
    security_tokens = SENSITIVE | frozenset({
        "alembic", "database", "db", "security", "secure", "secret",
        "credential", "permission", "ruleset", "codeowners",
    })
    if set(parts) & SENSITIVE or tokens & security_tokens:
        return HIGH, "security, data or operations-sensitive path"
    if tokens & {"ci", "workflow", "workflows", "pipeline", "codeql", "gitleaks"}:
        return MEDIUM, "CI or scanning verification requires review"
    if status == "D":
        return MEDIUM, "deletion requires review"
    if path.startswith(".github/workflows/"):
        return MEDIUM, "CI workflow change"
    if path in ("README.md", "CONTRIBUTING.md") or (
        path.startswith("docs/") and path.endswith(".md")
    ):
        return LOW, "ordinary documentation; inspect content"
    if (
        path.startswith("generator/tests/") and path.endswith(".test.mjs")
    ) or (
        path.startswith("tests/") and path.endswith((".py", ".mjs", ".ts", ".tsx"))
    ) or (
        path.startswith("scripts/tests/") and path.endswith(".py")
    ):
        return LOW, "test-only; verify assertions are not weakened"
    return MEDIUM, "source, dependencies, configuration or unknown path"

def classify_changes(changes: list[tuple[str, str]]) -> dict[str, object]:
    if not changes:
        return {"level": "HIGH", "reason": "empty diff; fail closed", "files": []}
    files = []
    overall = LOW
    for status, path in changes:
        level, reason = classify_path(path, status)
        overall = max(overall, level)
        files.append({"path": path, "status": status,
                      "level": LEVELS[level], "reason": reason})
    return {"level": LEVELS[overall], "files": files}

def git_changes(base_sha: str) -> list[tuple[str, str]]:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base_sha):
        raise ValueError("base must be an exact 40-character commit SHA")
    result = subprocess.run(
        ["git", "diff", "--name-status", "-z", "--no-renames",
         f"{base_sha}...HEAD"],
        capture_output=True, check=True,
    )
    fields = result.stdout.split(b"\0")
    if fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise ValueError("malformed git change record")
    return [
        (fields[i].decode("utf-8"), fields[i + 1].decode("utf-8"))
        for i in range(0, len(fields), 2)
    ]

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="exact PR base SHA")
    args = parser.parse_args()
    print(json.dumps(classify_changes(git_changes(args.base)),
                     indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
