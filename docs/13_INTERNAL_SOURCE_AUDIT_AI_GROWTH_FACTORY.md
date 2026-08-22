# Phase 1 — Internal Source Audit: AI Growth Factory

Status: ACTIVE AUDIT
Source repository: `niwarb06/ai-growth-factory`
Audit target: extract only generalized, tested patterns into DevForge. Do not copy product-specific business logic blindly.

## Current Reality
The repository is no longer planning-only. Current `main` contains an implemented FastAPI backend, Next.js frontend, PostgreSQL/Redis deployment stack, migrations, testing/lint tooling, and recent production/staging fixes.

## Confirmed Reusable Foundations

### Backend foundation — HIGH PRIORITY
Current backend declares:
- Python >= 3.12
- FastAPI / Uvicorn
- Pydantic Settings
- SQLAlchemy 2
- Alembic
- PostgreSQL + SQLite development support
- Redis
- bcrypt password hashing
- JWT
- pytest / httpx / Ruff / strict mypy
- provider integrations for OpenAI, Anthropic, and Gemini

DevForge action:
- extract configuration conventions;
- extract database/session/migration patterns;
- extract health/readiness patterns;
- extract test/lint/typecheck baseline;
- separate generic AI-provider abstraction from AGF-specific prompt/product logic.

### Frontend foundation — HIGH PRIORITY
Current frontend declares:
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Vitest + Testing Library
- explicit typecheck task
- secret scan and artifact scan scripts

DevForge action:
- inspect and generalize the protected app shell;
- extract responsive navigation patterns only after component cleanup;
- preserve secret/artifact scan concepts as default generator quality gates;
- extract test configuration and server/client boundary conventions.

### Deployment foundation — HIGH PRIORITY
Current production Compose stack includes:
- PostgreSQL 16 with persistent volume and healthcheck;
- Redis with password, AOF persistence, healthcheck;
- dedicated Alembic migration service before backend start;
- backend readiness healthcheck;
- frontend healthcheck;
- release-ID-tagged images;
- internal and edge networks;
- required environment-variable validation;
- staging/production service-name isolation.

DevForge action:
- create a provider-neutral Docker Compose baseline inspired by these patterns;
- keep migrations as an explicit release step;
- keep service health gating and environment isolation;
- remove all AGF-specific names, billing variables, AI provider settings, and domains.

## Reusable Candidate Inventory

| Candidate | Source | Initial state | Notes |
|---|---|---|---|
| FastAPI project baseline | `backend/` | CANDIDATE | Strong match with DevForge stack; needs product decoupling |
| SQLAlchemy + Alembic migration flow | `backend/` + Compose | CANDIDATE | High reuse value |
| PostgreSQL/Redis Compose baseline | `compose.production.yml`, staging equivalent | CANDIDATE | Generalize names, secrets, networks |
| Health/readiness checks | backend + Compose | CANDIDATE | Required for generated services |
| Python QA config | `backend/pyproject.toml` | CANDIDATE | Ruff + mypy + pytest baseline |
| Next.js QA config | `frontend/package.json` | CANDIDATE | Typecheck/test/security scans |
| Responsive protected shell | `frontend/app/(protected)/app/page.tsx` | EXPERIMENTAL | Product branding/navigation must be abstracted |
| AI provider abstraction | backend AI layer | CANDIDATE | Audit interfaces before reuse |
| Billing integration | product-specific | HOLD | Do not promote to core until adapterized |
| LinkedIn automation logic | product-specific | REJECT_FOR_CORE | Belongs only in product pack/integration if ever reused |

## Security / Design Findings

### Do not copy session lifetime defaults blindly
The production Compose currently exposes `ACCESS_TOKEN_EXPIRE_MINUTES` with a paid-beta default of 480 minutes. DevForge must make session policy product/security-profile driven rather than inherit an AGF beta default.

### Current code outranks stale planning documents
Older planning documents can describe Supabase/Vercel-era choices, while current implementation uses a FastAPI/PostgreSQL/Redis/Docker stack. DevForge audits must use current code and deployment files as the primary technical truth, with documents used only as supporting context.

### Product variables must be removed
AGF-specific values such as billing plan codes, provider choices, product names, domains, and marketing flows are not reusable core.

## Extraction Order
1. QA/tooling baseline
2. Backend configuration + database/migration skeleton
3. Docker/staging/production baseline
4. Health/readiness + observability skeleton
5. Web shell + API contract pattern
6. Auth/session module after dedicated security audit
7. AI provider adapter after interface audit

## Promotion Gate
Nothing from AI Growth Factory becomes `TRUSTED` in DevForge until it:
- is generalized and renamed;
- contains no AGF secrets/data/product assumptions;
- has module-level tests;
- meets DevForge Security Baseline;
- has a documented public contract;
- passes generated-app integration tests.
