# Niwar DevForge — Architecture Principles

## 1. Modular by default
Core capabilities, reusable feature modules, product packs, and provider adapters must remain separable. Product-specific business logic must not leak into shared modules.

## 2. Stable contracts
Modules communicate through explicit interfaces, API schemas, events, and versioned contracts. Internal implementation may change without forcing unrelated products to change.

## 3. Provider adapters
External services such as payments, maps, storage, notifications, identity verification, analytics, and AI providers must be integrated behind adapters where practical.

## 4. Secure defaults
Least privilege, deny-by-default authorization, secret isolation, encrypted transport, safe logging, auditability, dependency scanning, and production/staging separation are baseline requirements.

## 5. Reuse only after hardening
A feature becomes part of DevForge only after it is generalized, tested, documented, versioned, and stripped of customer/project-specific data and secrets.

## 6. Mobile/Web/Backend separation
Reference stack:
- Mobile: Flutter
- Web/Admin: Next.js + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- Cache/Jobs: Redis where justified
- Infrastructure: Docker + GitHub Actions

The architecture may support alternatives through adapters, but the canonical path stays narrow to reduce maintenance cost.

## 7. Localization from day one
Kurdish, Arabic, and English are first-class locales. RTL/LTR behavior must be tested, not patched later.

## 8. Observable systems
Every production service should support structured logs, request correlation, health checks, metrics, error reporting, and audit events appropriate to its risk level.

## 9. Migration safety
Database migrations are versioned, reviewable, forward-safe where possible, tested before production, and paired with backup/rollback procedures for risky changes.

## 10. Generated does not mean trusted
Generator or AI-created code must pass the same static analysis, tests, security gates, review rules, and release criteria as manually written code.

## 11. Production is a gated state
Prototype, MVP, staging, release candidate, and production are distinct states. A UI-complete application is not automatically production-ready.

## 12. Optimize total lifetime cost
Prefer a slightly slower reusable solution once over repeatedly shipping fragile shortcuts across many products.
