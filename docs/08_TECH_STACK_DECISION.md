# Niwar DevForge — Tech Stack Decision V1

## Purpose
Define the default stack for reusable DevForge products. Product-specific exceptions are allowed only when the benefit is documented.

## Default Product Stack

### Mobile
- Flutter / Dart
- Feature-first modular structure
- Typed API client
- Secure platform storage for tokens/secrets
- Localization from day one: Kurdish (Badini), Arabic, English

### Web / Admin
- Next.js + TypeScript
- App Router
- Tailwind CSS
- Accessible reusable design system
- Server/client boundaries chosen deliberately

### Backend
- FastAPI + Python
- Typed request/response schemas
- Layered domain/service/repository boundaries
- Async I/O where it materially helps

### Data
- PostgreSQL as the system of record
- Redis for cache, queues, locks, or ephemeral state when required
- Versioned migrations
- Explicit audit/ledger models for sensitive state

### Infrastructure
- Docker for reproducible local/staging/production services
- GitHub Actions for CI/CD
- Separate dev, staging, production environments
- Provider-neutral deployment where practical

## Provider Adapters
External providers are integrations, not the core domain. Use adapters for:
- Auth providers
- Object storage
- Push notifications
- Email/SMS/OTP
- Payments
- Maps/geocoding
- KYC/identity verification
- AI model providers
- Analytics/monitoring

The domain layer must not depend directly on a specific provider when an adapter boundary is reasonable.

## Supabase / Firebase Policy
Supabase or Firebase may accelerate specific products, but DevForge reusable business rules must not become irreversibly coupled to them. Public client keys are permitted only when provider security rules make them safe; privileged keys remain server-side.

## Monorepo Direction
DevForge itself is a reusable monorepo containing:
- apps/
- packages/
- packs/
- adapters/
- generator/
- agents/
- infrastructure/
- docs/

Generated customer/product repositories may be monorepos or split repositories depending on scale and deployment needs.

## Versioning
- DevForge modules use semantic versioning principles.
- Breaking module changes require migration notes.
- Generated apps record the exact DevForge/module versions used.

## Exception Rule
A stack exception must document:
1. why the default stack is insufficient;
2. expected benefit;
3. maintenance/security cost;
4. migration/exit plan where lock-in exists.
