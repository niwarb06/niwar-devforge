# Backend Core Module

- Name: backend-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: FastAPI services and generated backend products

## Purpose

Provides the reusable backend foundation for configuration, database access, health checks, request context, structured logging, identity persistence, password hashing, opaque sessions, role-based authorization, tenant access boundaries, user profiles, and typed API contracts.

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
- `RolePermissionPolicy` and `default_authorization_policy()`
- guarded `RoleAssignmentService`
- tenant-scoped `TenantAuthorizationService`
- user profile repository/contracts
- strict Pydantic API contracts
- deterministic OpenAPI export via `scripts/export_openapi.py`
- request context and JSON logging middleware

## Data Models and Migrations

- `devforge_users`
- `devforge_sessions`
- `devforge_user_roles`
- `devforge_tenants`
- `devforge_tenant_memberships`
- Alembic baseline `0001_backend_core_baseline`
- identity/session migration `0002_identity_sessions`
- role/tenant migration `0003_roles_tenants`

Session tokens are opaque. Only token digests are persisted.

## Permissions

- global `user`: self-profile read/write
- global `admin`: privileged wildcard; assignment is server-side guarded
- tenant `member`: tenant read plus self-profile permissions
- tenant `owner`: tenant read/write and membership management
- privileged role mutation requires `roles.manage`
- tenant operations require an active tenant and active membership unless the actor is a global admin
- authorization defaults to deny when a permission or role is unknown

## Security

- Passwords are hashed with Argon2id defaults.
- Raw session tokens are never stored in the database.
- Disabled users cannot resolve active sessions.
- Roles are persisted server-side; client-provided role state is not authoritative.
- Tenant authorization validates active tenant boundaries and active memberships.
- Global admins cannot bypass a missing/disabled tenant boundary.
- Web/mobile credential transport is intentionally outside this module and must follow `docs/16_AUTH_CORE_DECISION.md`.
- Authentication and authorization failures must not leak secrets or credentials.
- Production secrets and database passwords must be supplied outside source control.

## OpenAPI and Generated Clients

FastAPI OpenAPI is the transport-contract source of truth. See `OPENAPI_CLIENTS.md`. CI exports the schema on every backend-core change. Web/mobile generators must be approved and version-pinned before generated clients are promoted to reusable status.

## Tests and Quality Gates

CI runs Ruff, strict mypy, Alembic upgrade, deterministic OpenAPI export, pytest, and coverage against PostgreSQL and Redis service containers. Authorization tests cover privileged role assignment, tenant membership boundaries, and denial of cross-tenant or over-privileged access. The module remains EXPERIMENTAL until broader integration, failure-path, migration, generated-client, and production-like pilot evidence satisfy the DevForge module contract and quality gates.

## Upgrade Notes

Changes to auth contracts, persisted identity/session/role/tenant schema, session semantics, permission names, OpenAPI contracts, or migration history require explicit compatibility and rollback review before promotion to TRUSTED.
