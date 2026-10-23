# Niwar DevForge — PR Risk and Independent Review Proposal

**Status: advisory only; NOT an enforced GitHub merge gate.**

This proposal and its classifier do not modify the GitHub ruleset, enforce approvals, or authorize merges. Changes to this policy or classifier are themselves HIGH risk.

## GitHub protection gap observed 14 October 2026

The active protect-main ruleset disallows deletion and non-fast-forward and requires PRs with resolved review threads, but it requires only the required-pr-gate status check. Required approving review count is zero and strict up-to-date checks are disabled. Do **not** treat mergeable=true as full verification.

## Risk and decision

| Risk | Typical changes | Required decision |
|---|---|---|
| LOW | Ordinary documentation, isolated additive or non-weakening tests | Automated merge only after all exact-head push and PR CI is green, clean mergeability, content/diff review, no blockers |
| MEDIUM | GitHub Actions workflows (except protected required gate), generator/runtime/source, dependencies, dev configuration, deletions, unknown files | Independent HUMAN approval on exact latest head, full CI, no blockers; no autonomous merge without review |
| HIGH | Ruleset/branch protection, required gate, agent/security/quality policy, auth/identity/KYC, payments/wallet, credentials, migrations, staging/production/release or destructive work | Explicit user authorization plus independent human review and security/compatibility assessment; no autonomous merge |

The highest-risk changed file determines the entire PR risk. Renames or unknown statuses fail closed. A test-only path does not prove safe test assertions; weakening them invalidates LOW classification and must block merge. The advisory classifier treats security/database/authentication terms in **filenames as well as directories** as HIGH (including sensitive test files); CI/scanning filenames are at least MEDIUM. This remains a conservative hint, never approval to merge.

## Independent review rules

- The authoring agent's self-review, own GitHub comment, passing tests, or separate pass by the same agent do not constitute an independent HUMAN approval.
- AI review can provide additional evidence; do not claim it is an approved GitHub human review.
- Check reviewer approval against the latest exact head; any head change invalidates assumptions.
- If no reviewer is available, report as blocked. Never bypass required review.

## Pre-merge and post-merge

1. Re-fetch current main, PR head and base SHA, diff, review threads and security scope.
2. Inspect the actual patch and assign the highest risk; path classification is only advisory.
3. Ensure all applicable PR AND push checks for the exact head have finished successfully, including required-pr-gate, security and platform jobs. Pending, failed, cancelled and unexplained skipped checks block.
4. Ensure current base and clean mergeability; require independent review for MEDIUM/HIGH, explicit user authorization for HIGH.
5. LOW only: GitHub merge via expected_head_sha guard, then verify new main, signature, and post-merge checks.
6. Record evidence, continue with the next approved task; never change protected main directly, force-push or deploy.

## Optional advisory command

From a checked-out PR branch, run:
    python scripts/pr_risk_advisory.py --base <40-character-base-sha>

Run self-tests:
    python -m unittest discover -s scripts/tests -p 'test_pr_risk_advisory.py'

The script returns JSON about file-path risk only. It does NOT check CI, contents, security findings or human approvals and is NOT wired to required-pr-gate.

## Future GitHub ruleset changes — SEPARATE HIGH-risk request

After explicit authorization and independent review, consider requiring a suitable human approval and strict up-to-date CI or a verified aggregate required gate. Audit stable job names, path filtering and availability of an independent reviewer first: requiring every optional path-filtered workflow could deadlock ordinary PRs; requiring a human reviewer could deadlock a solo-maintainer project. Do not change or weaken protect-main/required-pr-gate in this proposal.
