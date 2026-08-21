# Niwar DevForge — Repository Structure

## Target Monorepo Layout

```text
niwar-devforge/
├─ apps/
│  ├─ mobile_flutter/
│  ├─ web_next/
│  ├─ admin_next/
│  └─ api_fastapi/
├─ packages/
│  ├─ contracts/
│  ├─ design_system/
│  ├─ localization/
│  ├─ auth/
│  ├─ users/
│  ├─ permissions/
│  ├─ notifications/
│  ├─ storage/
│  ├─ chat/
│  ├─ search/
│  ├─ maps/
│  ├─ payments/
│  ├─ subscriptions/
│  ├─ reviews/
│  ├─ media/
│  ├─ verification/
│  └─ observability/
├─ packs/
│  ├─ business/
│  ├─ booking/
│  ├─ marketplace/
│  ├─ dating/
│  ├─ delivery/
│  └─ ai_saas/
├─ adapters/
│  ├─ payments/
│  ├─ notifications/
│  ├─ storage/
│  ├─ maps/
│  ├─ otp/
│  ├─ verification/
│  └─ ai/
├─ generator/
├─ agents/
├─ infrastructure/
│  ├─ docker/
│  ├─ ci/
│  ├─ deploy/
│  ├─ monitoring/
│  └─ backup/
├─ tests/
│  ├─ integration/
│  ├─ e2e/
│  └─ security/
├─ docs/
├─ scripts/
└─ examples/
```

## Structural Rules
- `apps/` contains runnable reference applications, not product-specific applications.
- `packages/` contains provider-neutral reusable capabilities.
- `adapters/` contains external-provider implementations.
- `packs/` composes reusable modules for a product family and contains only generic family logic.
- `generator/` assembles a new product from manifests/templates.
- `agents/` contains instructions, guardrails, and automation workflows for AI-assisted engineering.
- `infrastructure/` owns reproducible development, CI/CD, deployment, monitoring, and backup assets.
- `examples/` demonstrates module composition without becoming production product code.

## Product Repositories
Generated products SHOULD live in separate repositories. DevForge remains the reusable source of truth. Product-specific changes return to DevForge only after generalization, testing, security review, and documentation.
