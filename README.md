# Niwar DevForge

Niwar DevForge is a reusable software-development foundation for building secure, scalable mobile, web, SaaS, marketplace, booking, social, delivery, business, and AI products without rebuilding common infrastructure for every project.

## Mission
Build reusable, tested, documented, provider-neutral modules once, then compose them into future products quickly and safely.

## Reference stack
- Mobile: Flutter / Dart
- Web and admin: Next.js / TypeScript
- Backend: FastAPI / Python
- Database: PostgreSQL
- Cache and coordination: Redis where justified
- Infrastructure: Docker
- CI/CD: GitHub Actions

External providers for payments, notifications, storage, maps, OTP, verification, AI, and analytics must sit behind DevForge-owned adapters.

## Current status
The repository is being built in ordered phases: foundation and governance; source and OSS audit; core platform; shared reusable modules; product packs; project generator; AI-agent automation; security/QA/CI-CD hardening; pilot proof from generation to production.

See [`docs/01_ROADMAP_0_TO_100.md`](docs/01_ROADMAP_0_TO_100.md) for the full roadmap.

## Engineering rules
- `main` is the stable line; work belongs on scoped branches and enters through reviewed pull requests.
- Do not commit secrets, private keys, production credentials, customer data, or product-specific sensitive data.
- Reuse DevForge-owned stable modules before importing third-party code or implementing duplicates.
- External code must pass OSS intake, provenance, license, security, dependency, and quality review.
- Database changes are migration-driven and destructive production changes require explicit approval and rollback planning.
- Generated or AI-written code is not trusted automatically; it must pass the same quality gates as human-written code.
- Reusable modules must remain product-neutral, documented, versioned, and independently testable.

## Core governance docs
- [`docs/02_ARCHITECTURE_PRINCIPLES.md`](docs/02_ARCHITECTURE_PRINCIPLES.md)
- [`docs/03_OSS_INTAKE_POLICY.md`](docs/03_OSS_INTAKE_POLICY.md)
- [`docs/04_SECURITY_BASELINE.md`](docs/04_SECURITY_BASELINE.md)
- [`docs/05_MODULE_CONTRACT.md`](docs/05_MODULE_CONTRACT.md)
- [`docs/07_AI_AGENT_RULES.md`](docs/07_AI_AGENT_RULES.md)
- [`docs/08_TECH_STACK_DECISION.md`](docs/08_TECH_STACK_DECISION.md)
- [`docs/09_QUALITY_GATES.md`](docs/09_QUALITY_GATES.md)
- [`docs/10_MODULE_CATALOG_V1.md`](docs/10_MODULE_CATALOG_V1.md)
- [`docs/11_AUDIT_SCORECARD.md`](docs/11_AUDIT_SCORECARD.md)
- [`docs/12_DEFINITION_OF_DONE.md`](docs/12_DEFINITION_OF_DONE.md)

## Development workflow
Read the relevant governance and module docs first, define a narrow change, implement it on a branch, run the required checks, document compatibility/security implications, and submit the result through a pull request. Repository-specific agent instructions live in [`AGENTS.md`](AGENTS.md).
