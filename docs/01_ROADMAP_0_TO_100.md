# Niwar DevForge — Roadmap 0 → 100

## Goal
Create a durable reusable platform that reduces repeated engineering across future products while preserving security, quality, and provider independence.

## Phase 0 — Foundation (0–10%)
Exit criteria:
- Vision, architecture, module contract, OSS policy, security baseline, agent workflow approved.
- Repository structure defined.
- Initial reusable module catalog defined.

## Phase 1 — Source Audit (10–20%)
- Audit reusable assets from existing internal projects.
- Audit candidate open-source projects/components.
- Record license, maintenance, security, dependency, and reuse decisions.
- Never import code before license/security review.

## Phase 2 — Core Platform (20–45%)
Build shared foundations:
- Identity/authentication
- Users/profiles
- Roles/permissions
- Localization (ku/ar/en)
- Configuration/secrets
- API client/contracts
- Storage/uploads
- Notifications
- Audit logging
- Observability
- Error handling

## Phase 3 — Shared Feature Modules (45–65%)
- Chat/realtime
- Maps/location
- Search/filter
- Reviews/ratings
- Payments abstraction
- Subscriptions
- Wallet ledger abstraction
- Media
- Verification/KYC abstraction

## Phase 4 — Product Packs (65–78%)
- Business/CRUD
- Booking/property
- Marketplace/commerce
- Dating/social
- Delivery/logistics
- AI/SaaS

## Phase 5 — Generator (78–86%)
A deterministic project generator selects core + modules + pack and emits:
- Mobile/Web/Admin/Backend scaffolds
- Database migrations
- Environment examples
- Test skeletons
- CI workflows
- Docker/dev setup
- Documentation manifest

## Phase 6 — AI Agent Automation (86–92%)
Agents may scaffold, implement, test, audit, document, and prepare PRs under repository rules. Human approval remains required for security-sensitive, data-destructive, payment, and production-release changes.

## Phase 7 — Security / QA / CI-CD (92–97%)
- SAST/dependency/secret scanning
- Unit/integration/e2e tests
- Migration safety checks
- Release gates
- Staging before production
- Rollback and backup validation

## Phase 8 — Pilot Proof (97–100%)
Build at least two materially different pilot products from DevForge. Measure:
- % reused code/modules
- time to first working build
- time to production candidate
- defects/regressions
- custom code required

## Continuous Rule
Every new project must return reusable improvements to DevForge only after they are generalized, tested, documented, and stripped of product-specific secrets/data.
