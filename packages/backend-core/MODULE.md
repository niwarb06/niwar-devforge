# Backend Core Module

- Name: backend-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: FastAPI services and generated backend products

## Purpose

Provides the reusable backend foundation for configuration, database access, health checks, request context, structured logging, identity persistence, password hashing, and opaque sessions.

## Dependencies

FastAPI, Pydantic Settings, SQLAlchemy, Alembic, psycopg, Redis client, Argon2, Uvicorn.

## Configuration

All runtime settings use the `DEVFORGE_` environment prefix. Production and shared environments must supply real database and infrastructure credentials through secret management. No real credentials belong in this repository.

## Public Interfaces

- `create_app()` FastAPI application factory
- `Settings` / `get_settings()`
- database engine/session builders and `get_db()`
- health router: `/health/live`, `/health/ready`
- auth contracts and `AuthService`
- `SqlAlchemyUserRepository`
- `Argon2Hasher`
- `DatabaseSessionIssuer`
- request context and JSON logging middleware

## Data Models and Migrations

- `devforge_users`
- `devforge_sessions`
- Alembic baseline `0001_backend_core_baseline`
- identity/session migration `0002_identity_sessions`

Session tokens are opaque. Only token digests are persisted.

## Security

- Passwords are hashed with Argon2id defaults.
- Raw session tokens are never stored in the database.
- Disabled users cannot resolve active sessions.
- Web/mobile credential transport is intentionally outside this module and must follow `docs/16_AUTH_CORE_DECISION.md`.
- Authentication and authorization failures must not leak secrets or credentials.
- Production secrets and database passwords must be supplied outside source control.

## Tests and Quality Gates

CI runs Ruff, strict mypy, Alembic upgrade, pytest, and coverage against PostgreSQL and Redis service containers. The module remains EXPERIMENTAL until broader integration, failure-path, migration, and production-like pilot evidence satisfy the DevForge module contract and quality gates.

## Upgrade Notes

Changes to auth contracts, persisted identity/session schema, session semantics, or migration history require explicit compatibility and rollback review before promotion to TRUSTED.
