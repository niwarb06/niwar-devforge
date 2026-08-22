# Backend Core Module

- Name: backend-core
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: FastAPI services and generated backend products

## Purpose

Provides the reusable backend foundation for configuration, database access, health checks, request context, structured logging, identity persistence, password hashing, opaque sessions, role-based authorization, tenant access boundaries, user profiles, typed API contracts, and authenticated API transport primitives.

## Dependencies

FastAPI, Pydantic Settings, SQLAlchemy, Alembic, psycopg, Redis client, Argon2, Uvicorn.

## Configuration

All runtime settings use the `DEVFORGE_` environment prefix. Production and shared environments must supply real database and infrastructure credentials through secret management. No real credentials belong in this repository.

- `DEVFORGE_SESSION_TTL_MINUTES` controls opaque session lifetime. The default remains 10,080 minutes for compatibility with the existing experimental behavior and can be tightened by product policy.

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
- `get_authenticated_session()` / `get_current_actor()` API dependencies
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me/profile`
- `DELETE /api/v1/auth/session`
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

- Passwords are hashed with Argon2id defaults.
- Raw session tokens are never stored in the database.
- Session resolution loads current persisted roles instead of trusting role state captured at login time.
- Disabled users cannot resolve active sessions.
- Roles are persisted server-side; client-provided role state is not authoritative.
- Tenant authorization validates active tenant boundaries and active memberships.
- Tenant-scoped roles are namespaced so membership roles cannot be mistaken for global roles.
- Global admins cannot bypass a missing or disabled tenant boundary.
- The `DevForgeSession` bearer scheme is for mobile/API/server-to-server transport. Browser JavaScript must not receive or persist opaque session credentials; web products use the server-mediated BFF + Secure/HttpOnly cookie design from `docs/16_AUTH_CORE_DECISION.md`.
- Logout revokes the presented opaque session server-side.
- Authentication and authorization failures use generic typed API errors and must not leak secrets or credentials.
- Incoming `X-Request-ID` values are accepted only when they match the bounded safe character policy; malformed or oversized values are replaced with a server-generated UUID before logging or echoing.
- DevForge logging is configured on the `devforge` logger without clearing host/root handlers, and repeated configuration does not add duplicate DevForge handlers.
- Production secrets and database passwords must be supplied outside source control.

## OpenAPI and Generated Clients

FastAPI OpenAPI is the transport-contract source of truth. See `OPENAPI_CLIENTS.md`. CI exports the schema on every backend-core change. The authenticated profile and logout routes now provide concrete protected contracts for downstream client-generation proof. Web/mobile generators must be approved and version-pinned before generated clients are promoted to reusable status.

## Tests and Quality Gates

CI runs Ruff, strict mypy, Alembic upgrade, deterministic OpenAPI export, pytest, and coverage against PostgreSQL and Redis service containers. Authorization tests cover privileged role assignment, tenant membership boundaries, tenant/global role isolation, and denial of cross-tenant, inactive-tenant, or over-privileged access. API tests cover unauthenticated denial, persisted-role session resolution, self-profile read/update, logout revocation, and OpenAPI security metadata. Observability tests cover malformed/oversized request-ID replacement plus idempotent logging configuration that preserves host handlers. The module remains EXPERIMENTAL until broader credential-route/rate-limit tests, generated-client proof, web BFF transport, failure-path coverage, and production-like pilot evidence satisfy the DevForge module contract and quality gates.

## Upgrade Notes

Changes to auth contracts, persisted identity/session/role/tenant schema, session lifetime defaults, session transport, permission names, OpenAPI contracts, or migration history require explicit compatibility and rollback review before promotion to TRUSTED.
