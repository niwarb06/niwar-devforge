# Niwar DevForge — PR Risk and Solo-Maintainer AI Review Policy

**Status:** This is a repository operating policy **only once merged to protected `main`**. Until then it is a proposal on PR #79. This document does not itself edit the GitHub `protect-main` ruleset or the required CI gate.

## Owner decision and review identity

The sole owner explicitly requested on **2026-11-18** that DevForge no longer require a second human reviewer for AI-assisted PR review and safe completion. Under this owner-delegated, single-maintainer workflow, the assistant may inspect, record a **technical AI approval**, and merge eligible PRs only after all mandatory safeguards below succeed.

- **AI review is NOT an independent human approval or GitHub `APPROVED` review.** It is logged truthfully as an AI technical verdict in a `COMMENTED` PR review or auditable PR comment, with exact reviewed SHA and evidence.
- The connected GitHub account may also be the PR author; do not attempt author self-approval through GitHub `APPROVE`, invent a second person, or imply AI is human.
- The owner accepts the **loss of an independent human second pair of eyes** as a deliberate governance tradeoff, not evidence that the residual risk is zero. Automated tests complement, not guarantee, security review.
- Branch-protection rules, required checks, licenses, confidentiality and security policies still apply. Never silently override an actual required GitHub approval.

## Risk classes and authorization

| Risk | Typical scope | Decision under this policy |
|---|---|---|
| LOW | Ordinary documentation, narrowly additive tests with intact assertions | AI technical review and **all exact-head applicable push + PR checks** must pass; agent may merge with expected-head SHA guard |
| MEDIUM | Generator/source/runtime and same-major pinned dependency updates, normal CI workflow changes other than the protected required gate | Comprehensive AI source/security/dependency review **plus all applicable exact-head PR and push checks, actual logs, and compatibility evidence**; agent may merge after an auditable AI technical approval and verified no blockers |
| HIGH | Governance, branch protection/required gate, authentication/identity/permissions, secrets, KYC/payments/wallet, migrations, production/staging/release, destructive actions | **Explicit owner authorization for the specific scope**, comprehensive security/compatibility and rollback review, and all applicable evidence and checks. No blanket autonomous approval or implicit HIGH merge. A separate human reviewer is recommended but **not mandatory under the owner's amended rule**. If the action involves production, secrets, access broadening, destructive data, or weakening any quality/security control, its existing explicit authorization and safety constraints still apply |

The highest-risk file **or behavior** determines the entire PR risk; an advisory path classifier is not a security proof. Unknown files, renames, deletions, sensitive filenames, governance and required-gate changes must be conservatively classified. No change that disables tests, masks failures, suppresses scans, bypasses authorization, or weakens required quality/security gates is eligible for automatic completion.

**One-time adoption of this HIGH governance change:** The owner's 2026-11-18 request explicitly authorizes proposing and, once the exact resulting PR is comprehensively reviewed and all required safeguards pass, adopting this solo-maintainer AI-review rule by a protected-branch PR merge. Record the exact head and owner-delegation context in that PR. This does not pre-authorize other HIGH PRs or production/deployment operations.

## Mandatory pre-merge checklist — every risk class

1. Re-read repository instructions and inspect the **actual entire patch**, files changed, surrounding contracts, relevant vendor advisories, dependencies, permissions, scope and security/data risks. Record the current protected `main`, base SHA, PR head SHA, author, risk class and any blocking findings.
2. Confirm PR is open, not draft, cleanly mergeable, has no unresolved review threads, no unreviewed scope expansion and no stale blocking approval/change request. Do not bypass repository branch protections.
3. Query GitHub Actions and check-runs **for the exact current head**; **every applicable PR and push workflow**, quality/security test, required PR gate, CodeQL, secrets/dependency and supply-chain scan, build, typecheck, integration, platform test and vulnerability audit must be finished successfully. If a workflow is expected but missing, investigate; a green aggregate badge is not enough. Failed, cancelled, pending, timed-out, skipped or unexplained neutral checks block.
4. Examine **real job logs**, not only badges, for important audit and runtime results; verify dependency versions, transitive risks, vendor security status and application compatibility. Record known flaky tests distinctly; passing on retry does not prove the flake fixed. Any unresolved significant new vulnerability or compatibility defect blocks.
5. Submit a **truthfully identified AI technical approval / no-blockers review as `COMMENTED`**, anchored to the exact latest head. Include scope, risk, evidence URLs, residual risks and merge decision. If checks fail or uncertainty is material, write BLOCKED instead of approval.
6. For **HIGH**, check documented, explicit owner scope authorization before merge, and assess rollback; never infer permission from a general desire for faster progress. Keep release/deployment, credential rotation, destructive operations and direct changes to protected `main` out of autonomous merge operations.
7. Immediately before merge re-fetch PR head and base SHA, current `main`, check runs, security alerts, review-thread state and mergeability. If **head or base drift** invalidates prior tests, stop and re-run/review; never rely on stale checks after substantive base changes.
8. Merge **only through the GitHub pull-request API**, using `expected_head_sha`; no direct writes to protected `main`, branch deletion, force-push, CI gate edits or deployment. If the merge guard rejects, stop and investigate rather than forcing it.
9. Verify GitHub reports `merged=true`, inspect resulting `main` commit and signature when available, required checks/post-merge evidence, and outstanding security alerts. Log exact outcome and remaining problems. Never claim success before verification.

## Existing protections and stop conditions

- Preserve `AGENTS.md`, `docs/04_SECURITY_BASELINE.md`, `docs/07_AI_AGENT_RULES.md`, `docs/09_QUALITY_GATES.md`, `docs/12_DEFINITION_OF_DONE.md` and `.github/workflows/required-pr-gate.yml`; stronger module-specific safety constraints override this operational policy.
- PR #66 remains excluded from all edits/merges unless separately authorized.
- Dependency remediation PRs must keep production and development `npm audit`, supply-chain scanning and genuine device/integration testing.
- A blocked PR remains open with reasons; never relabel `COMMENTED` as `APPROVED`, forge human identity, or dismiss a vulnerability merely because CI is green.
- Repo-wide automatic merge features are not enabled by this document. Each safe PR requires a fresh per-head review and final guarded merge decision.

## Advisory risk classifier

Run from a checked-out PR branch:

```sh
python scripts/pr_risk_advisory.py --base <40-character-base-sha>
python -m unittest discover -s scripts/tests -p 'test_pr_risk_advisory.py'
```

The classifier is **advisory-only** and intentionally fail-closed on sensitive or unknown paths. It does not determine approval, bypass tests, or modify GitHub rulesets.
