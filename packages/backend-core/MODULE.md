# Backend Core Module

- Name: backend-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: FastAPI services and generated backend products

## Purpose

Provides the reusable backend foundation for configuration, database access, health checks, request context, structured logging, identity persistence, password hashing, opaque sessions, role-based authorization, tenant access boundaries, user profiles, typed API contracts, authenticated API transport primitives, and credential abuse protection.

## Dependencies

FastAPI, Pydantic Settings, SQLAlchemy, Alembic, psycopg, Redis client, Argon2, Uvicorn.

## Configuration

All runtime settings use the `DEVFORGE_` environment prefix. Production and shared environments must supply real database and infrastructure credentials through secret management. No real credentials belong in this repository.

- `DEVFORGE_SESSION_TTL_MINUTES` controls opaque session lifetime. The default remains 10,080 minutes for compatibility with the existing experimental behavior and can be tightened by product policy.
- `DEVFORGE_AUTH_LOGIN_IDENTIFIER_LIMIT` and `DEVFORGE_AUTH_LOGIN_SOURCE_LIMIT` control login attempts per identifier and source within `DEVFORGE_AUTH_LOGIN_WINDOW_SECONDS`.
- `DEVFORGE_AUTH_REGISTER_IDENTIFIER_LIMIT` and `DEVFORGE_AUTH_REGISTER_SOURCE_LIMIT` control registration attempts within `DEVFORGE_AUTH_REGISTER_WINDOW_SECONDS`.
- `DEVFORGE_AUTH_TRUST_PROXY_HEADERS=false` is the safe default. Enable it only when a trusted reverse proxy overwrites/sanitizes `X-Forwarded-For`; otherwise the application uses the direct peer address for source limiting.

## Public Interfaces

- `create_app()` FastAPI application factory
- `Settings` / `get_settings()`
- database engine/session builders and `get_db()`
- health router: `/health/live`, `/health/ready`
- auth contracts and `AuthService`
- `SqlAlchemyUserRepository`
- `Argon2Hasher`
- `DatabaseSessionIssuer`
- `RedisFixedWindowRateLimiter` / `RateLimiter`
- `RolePermissionPolicy` and `default_authorization_policy()`
- guarded `RoleAssignmentService`
- tenant-scoped `TenantAuthorizationService`
- `get_authenticated_session()` / `get_current_actor()` API dependencies
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `DELETE /api/v1/auth/session`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me/profile`
- user profile repository/contracts
- strict Pydantic API contracts and typed API error responses
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
- tenant membership `member` maps to policy role `tenant:member`
- tenant membership `owner` maps to policy role `tenant:owner`
- `tenant:member`: tenant read plus self-profile permissions
- `tenant:owner`: tenant read/write and membership management
- privileged global-role mutation requires `roles.manage`
- tenant operations require an active tenant and active membership unless the actor is a global admin
- tenant membership roles are validated server-side and kept separate from global role names
- authorization defaults to deny when a permission or role is unknown

## Security

- Passwords are hashed with Argon2id defaults and never logged.
- Raw session tokens are never stored in the database.
- Session resolution loads current persisted roles instead of trusting role state captured at login time.
- Disabled users cannot resolve active sessions.
- Credential routes apply distributed Redis-backed fixed-window rate limits by source and identifier.
- Rate-limit Redis keys contain SHA-256 fingerprints rather than plaintext email/identifier values.
- Credential routes fail closed with a typed `503 auth_service_unavailable` response when abuse protection is unavailable.
- Duplicate-email registration deliberately returns the same `202 {"accepted": true}` response as a new registration and never changes an existing account.
- Login failures use a generic `401 invalid_credentials` response.
- Credential success/error responses use `Cache-Control: no-store`; `429` responses include `Retry-After`.
- `X-Forwarded-For` is ignored by default and is trusted only when `DEVFORGE_AUTH_TRUST_PROXY_HEADERS=true`.
- Roles are persisted server-side; client-provided role state is not authoritative.
- Tenant authorization validates active tenant boundaries and active memberships.
- Tenant-scoped roles are namespaced so membership roles cannot be mistaken for global roles.
- Global admins cannot bypass a missing or disabled tenant boundary.
- The `DevForgeSession` bearer scheme is for mobile/API/server-to-server transport. Browser JavaScript must not receive or persist opaque session credentials; web products use the server-mediated BFF + Secure/HttpOnly cookie design from `docs/16_AUTH_CORE_DECISION.md`.
- Logout revokes the presented opaque session server-side.
- Production secrets and database passwords must be supplied outside source control.

## OpenAPI and Generated Clients

FastAPI OpenAPI is the transport-contract source of truth. See `OPENAPI_CLIENTS.md`. CI exports the schema on every backend-core change and runs the pinned TypeScript generation proof against credential, profile, and logout contracts. Web/mobile generators must be approved and version-pinned before generated clients are promoted to reusable status.

## Tests and Quality Gates

CI runs Ruff, strict mypy, Alembic upgrade, deterministic OpenAPI export, TypeScript contract generation, pytest, and coverage against PostgreSQL and Redis service containers. Authorization tests cover privileged role assignment, tenant membership boundaries, tenant/global role isolation, and denial of cross-tenant, inactive-tenant, or over-privileged access. API tests cover credential registration/login behavior, generic duplicate-registration semantics, invalid credentials, source/identifier rate limits, fail-closed limiter behavior, session use, unauthenticated denial, persisted-role session resolution, self-profile read/update, logout revocation, OpenAPI security metadata, and hashed Redis limiter keys.

The module remains EXPERIMENTAL until email verification/password reset, web BFF cookie transport, Flutter client proof, broader failure-path/security review, and production-like pilot evidence satisfy the DevForge module contract and quality gates.

## Upgrade Notes

Changes to auth contracts, rate-limit defaults, proxy trust behavior, persisted identity/session/role/tenant schema, session lifetime defaults, session transport, permission names, OpenAPI contracts, or migration history require explicit compatibility and rollback review before promotion to TRUSTED.
