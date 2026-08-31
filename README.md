# Niwar DevForge

Niwar DevForge is a reusable software-development foundation for building secure, scalable mobile, web, SaaS, marketplace, booking, social, delivery, business, and AI products without rebuilding common infrastructure for every project.

## Mission

Build reusable, tested, documented, provider-neutral modules once, then compose them into future products quickly and safely.

## Reference stack

- Mobile: Flutter / Dart
- Web and admin: Next.js / TypeScript
- Backend: FastAPI / Python
- Database: PostgreSQL
- Cache and coordination: Valkey through a Redis-compatible RESP/client contract where justified
- Infrastructure: Docker
- CI/CD: GitHub Actions

External providers for payments, notifications, storage, maps, OTP, verification, AI, and analytics must sit behind DevForge-owned adapters.

## Current status

The repository is under active development and is being built in ordered phases:

1. Foundation and governance
2. Source and OSS audit
3. Core platform
4. Shared reusable modules
5. Product packs
6. Project generator
7. AI-agent automation
8. Security, QA, CI/CD hardening
9. Pilot proof from generation to production

See [`docs/01_ROADMAP_0_TO_100.md`](docs/01_ROADMAP_0_TO_100.md) for the full roadmap. Public source availability does not mean every module is stable or production-ready; module status and release gates remain authoritative.

## Repository model

The target monorepo contains runnable reference apps, provider-neutral packages, external-provider adapters, product packs, generator tooling, AI-agent workflows, infrastructure, tests, docs, scripts, and examples. See [`docs/06_REPOSITORY_STRUCTURE.md`](docs/06_REPOSITORY_STRUCTURE.md).

## Engineering rules

- `main` is the stable line; work belongs on scoped branches and enters through reviewed pull requests.
- Do not commit secrets, private keys, production credentials, customer data, or product-specific sensitive data.
- Reuse DevForge-owned stable modules before importing third-party code or implementing duplicates.
- External code must pass the OSS intake, provenance, license, security, dependency, and quality review.
- Database changes are migration-driven and destructive production changes require explicit approval and rollback planning.
- Generated or AI-written code is not trusted automatically; it must pass the same tests and quality gates as human-written code.
- Reusable modules must remain product-neutral, documented, versioned, and independently testable.

## Open-source use

DevForge-owned source is licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Apache-2.0 permits use, modification, redistribution, and commercial use subject to its terms, including preservation of required license and notice material. It does not relicense third-party dependencies or grant trademark rights beyond the license's limited terms.

Third-party software remains under its own upstream licenses. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and module-specific third-party reviews before redistributing packages, containers, or generated products.

For contributions, see [`CONTRIBUTING.md`](CONTRIBUTING.md). For vulnerabilities, follow [`SECURITY.md`](SECURITY.md) and do not disclose exploit details publicly. The current public-readiness boundary and release-time checks are documented in [`docs/19_OPEN_SOURCE_READINESS.md`](docs/19_OPEN_SOURCE_READINESS.md).

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
