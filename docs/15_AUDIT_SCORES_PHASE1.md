# Phase 1 — Audit Scores

Scoring follows `docs/11_AUDIT_SCORECARD.md`. Scores are evidence-based snapshots, not permanent endorsements.

## Candidate A — AI Growth Factory internal foundation

Source: `niwarb06/ai-growth-factory` (`main`, current implementation reviewed during Phase 1)
License gate: Internal source; reusable inside DevForge subject to product-data/secret stripping.
Decision: **ADAPT**

| Category | Max | Score | Evidence / concern |
|---|---:|---:|---|
| Functional Fit | 20 | 19 | FastAPI, PostgreSQL, Redis, Next.js, migrations, auth shell, Docker environments, scans |
| Code Quality / Architecture | 15 | 12 | Good typed/tooling baseline; some product-specific coupling remains |
| Security | 15 | 13 | Same-origin auth guards, no-store auth responses, server-only session handling; session policy needs generalization |
| Maintainability | 10 | 9 | Active current implementation and recent fixes |
| Test Quality | 10 | 8 | pytest/Vitest and focused static security tests present; DevForge needs broader reusable-module integration tests |
| Dependency Health | 10 | 9 | Current Python/Next.js/PostgreSQL/Redis stack |
| Reusability | 10 | 7 | Strong patterns but AGF naming/billing/AI/product flows must be removed |
| Documentation | 5 | 4 | Extensive planning/docs, though some older stack decisions are stale |
| Performance / Scalability | 5 | 4 | VPS-oriented health-gated Compose is useful; scale patterns still product-dependent |
| **Total** | **100** | **85** | **Strong internal source after generalization** |

### Adopt/adapt
- Python QA baseline: pytest + Ruff + strict mypy.
- Next.js typecheck/test/security-scan concepts.
- PostgreSQL/Redis health-gated Compose pattern.
- Dedicated migration service before backend startup.
- Staging/production service isolation.
- Server-side web session/BFF approach where tokens are not returned to browser JavaScript.
- Same-origin protection and `Cache-Control: no-store` on credential/logout routes.
- Protected-page recovery behavior after logout/history restoration.

### Do not copy directly
- 480-minute paid-beta access-token default.
- AGF product names, domains, billing plan codes, LinkedIn flows, AI prompts.
- Product-specific CSS/bootstrap workarounds as generic architecture.

---

## Candidate B — Vinta Next.js FastAPI Template

Source: `vintasoftware/nextjs-fastapi-template` (`main` reviewed during Phase 1)
License: MIT
Decision: **ADAPT SELECTED PARTS**

| Category | Max | Score | Evidence / concern |
|---|---:|---:|---|
| Functional Fit | 20 | 18 | FastAPI + Next.js, auth, typed OpenAPI client, Docker, tests, CI |
| Code Quality / Architecture | 15 | 13 | Clear async backend and typed frontend direction |
| Security | 15 | 10 | JWT/password recovery foundation is useful, but sample code logs a verification token and uses bearer transport; must not be copied blindly |
| Maintainability | 10 | 9 | Organized maintained template with CI/release workflows |
| Test Quality | 10 | 9 | Backend/frontend CI with coverage |
| Dependency Health | 10 | 9 | Modern Python/TypeScript tooling; dependencies still require pin/security review on intake |
| Reusability | 10 | 9 | Template is intentionally generic and typed |
| Documentation | 5 | 5 | Strong README/docs and setup guidance |
| Performance / Scalability | 5 | 4 | Async design is strong; `NullPool` is optimized for serverless and is not DevForge's universal VPS default |
| **Total** | **100** | **86** | **Strong source of patterns, not a wholesale import** |

### Adopt/adapt
- OpenAPI → typed frontend client concept.
- Zod/type-safe boundary concepts.
- CI split between backend and frontend.
- Pre-commit/quality automation ideas.
- Async SQLAlchemy session patterns after adapting pool strategy.
- Generic authentication lifecycle concepts (registration, reset, verification) after DevForge security redesign.

### Reject/remediate before reuse
- Never log verification/reset/authentication tokens.
- Do not make bearer tokens accessible to browser JavaScript by default for DevForge web apps.
- Do not hard-code serverless `NullPool` as the universal database configuration.
- Do not assume one auth library is the permanent domain contract; keep DevForge identity behind interfaces.

---

## Candidate C — bizz84 Flutter reference architecture

Source: `bizz84/starter_architecture_flutter_firebase`
License: MIT
Decision: **REFERENCE / ADAPT PATTERNS**

| Category | Max | Score | Evidence / concern |
|---|---:|---:|---|
| Functional Fit | 20 | 13 | Auth, CRUD, routing, Firebase persistence; not a generic DevForge starter out of the box |
| Code Quality / Architecture | 15 | 13 | Useful feature-first/repository/Riverpod architecture reference |
| Security | 15 | 10 | Standard Firebase model; full DevForge security posture still requires separate audit |
| Maintainability | 10 | 5 | README explicitly describes the project as low priority |
| Test Quality | 10 | 5 | README notes missing tests |
| Dependency Health | 10 | 8 | Common Flutter packages, but versions require intake verification |
| Reusability | 10 | 7 | Architecture is reusable; Firebase coupling must stay behind adapters |
| Documentation | 5 | 5 | Strong educational architecture documentation |
| Performance / Scalability | 5 | 3 | Useful reference, not evidence of broad production-scale behavior |
| **Total** | **100** | **69** | **Reference value; do not copy as DevForge core** |

## Phase 1 Selection

The first DevForge implementation will be a **hybrid**, not a fork:
1. Take AGF's proven VPS/deployment/security patterns.
2. Take Vinta's type-safe API/CI/template ideas.
3. Take Flutter architectural ideas from vetted references without coupling DevForge to Firebase.
4. Implement DevForge-owned contracts and tests so future providers/templates are replaceable.
