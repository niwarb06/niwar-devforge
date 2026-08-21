# Niwar DevForge — AI Agent Rules

## Purpose
AI agents accelerate engineering without becoming an uncontrolled source of architectural drift, licensing risk, security regressions, or production damage.

## Allowed by Default
Agents may:
- inspect repository state and documentation;
- search for reusable internal modules and approved open-source candidates;
- scaffold code from DevForge manifests/templates;
- implement isolated features on non-protected branches;
- add/update tests and documentation;
- run static checks, tests, linters, type checks, builds, and security scans;
- prepare commits and pull requests with a clear change summary;
- suggest dependency upgrades with compatibility notes.

## Explicit Approval Required
Agents must obtain explicit approval before:
- destructive database/data changes;
- secret rotation or credential changes;
- production deployment or rollback;
- payment-provider production configuration changes;
- authentication/authorization policy changes that broaden access;
- importing code whose license is not already approved;
- force-push, branch deletion, history rewrite, or direct protected-branch mutation;
- disabling tests, security checks, audit logs, backups, or rate limits.

## Never Allowed
Agents must never:
- commit real secrets or private keys;
- fabricate test/scan results;
- silence failures merely to make CI green;
- copy proprietary/decompiled application code into DevForge;
- bypass licensing obligations;
- claim production readiness without passing defined gates;
- modify unrelated product behavior while solving a scoped task without documenting and justifying it.

## Work Protocol
1. Read the task and relevant architecture/module docs.
2. Inspect current repository state before editing.
3. Define scope and acceptance checks.
4. Make the smallest coherent change.
5. Run relevant tests/checks.
6. Report exact results and remaining risks.
7. Update docs/contracts if public behavior changed.
8. Prefer PR-based review for material changes.

## Reuse Protocol
Before building a common capability from scratch, agents should check in order:
1. Stable DevForge module
2. Beta/experimental DevForge module
3. Existing internal project suitable for generalization
4. Approved open-source candidate
5. New implementation

Reuse is accepted only when compatibility, security, license, and maintenance cost are better than a clean implementation.

## Open-Source Intake
An agent proposing OSS reuse must record:
- repository/source;
- exact commit/tag when practical;
- license;
- maintenance freshness;
- known security/dependency concerns;
- what code/assets are actually being reused;
- modifications made;
- attribution obligations;
- reason reuse is better than rebuilding.

## Definition of Done for Agent Work
A task is not done until:
- requested behavior exists;
- relevant tests/checks pass or failures are explicitly reported;
- no new secret/license/security violation is known;
- scope remains controlled;
- docs/contracts are updated when needed;
- a reviewer can understand what changed and why.
