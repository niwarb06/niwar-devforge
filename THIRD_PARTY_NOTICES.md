# Third-Party Notices

Niwar DevForge source code is licensed under Apache-2.0 unless a file or bundled third-party component says otherwise. Third-party software remains under its own license; the DevForge license does not replace or relicense those components.

This file is a high-level direct-dependency and infrastructure inventory for the current foundation. It is not a substitute for the authoritative license text shipped by each dependency, and it is not a complete transitive SBOM. Every formal release must regenerate and review its exact dependency/license inventory.

## Core runtime and tooling

| Component | Current use | Upstream license / boundary |
| --- | --- | --- |
| FastAPI | Backend framework | MIT |
| Uvicorn | ASGI server | BSD-3-Clause |
| Pydantic / pydantic-settings | Validation/configuration | MIT |
| SQLAlchemy | ORM/database toolkit | MIT |
| Alembic | Database migrations | MIT |
| Psycopg 3 / psycopg-binary | PostgreSQL Python driver | LGPL-3.0-only; remains a separately licensed dependency and must retain applicable LGPL notices/terms when redistributed |
| redis-py (`redis` Python package) | RESP client used by backend code | MIT; this is a client library, not the Redis server |
| argon2-cffi | Password hashing binding | MIT; upstream distributions may include separately licensed/CC0 components and their notices must be preserved where applicable |
| PostgreSQL | Database server image/service | PostgreSQL License |
| Valkey 7.2.14 | Default cache/coordination server baseline | BSD-3-Clause; accessed through the Redis-compatible RESP protocol |
| Caddy | Staging TLS/reverse proxy | Apache-2.0 |
| Next.js | Web framework | MIT |
| React / React DOM | Web UI runtime | MIT |
| TypeScript | Type system/compiler | Apache-2.0 |
| Playwright | Browser test tooling | Apache-2.0 |
| flutter_secure_storage 10.3.1 | Mobile secure session storage adapter | BSD-3-Clause; see `packages/flutter-auth-core/THIRD_PARTY.md` |
| OpenAPI Generator CLI 7.24.0 | Ephemeral Dart contract-generation proof | Apache-2.0; exact JAR digest and boundary documented in `packages/flutter-auth-core/THIRD_PARTY.md` |

## GitHub Actions

Remote GitHub Actions are treated as executable supply-chain dependencies. DevForge workflows pin reviewed remote actions to full commit SHAs. Comments may record a human-readable upstream major version, but the executable reference is the immutable SHA.

## Redis server history

Earlier repository history and CI proofs used Redis Community Edition 7.4 server images. Redis 7.4 is offered under RSALv2 or SSPLv1 rather than an OSI-approved open-source license. The current open-source baseline therefore uses Valkey 7.2.14 (BSD-3-Clause) while retaining Redis-compatible client/protocol contracts where practical.

Do not assume an existing Redis 7.4 persistent RDB/AOF volume can be mounted directly into Valkey 7.2. A real deployment migrating existing data must follow a separately validated migration procedure rather than reusing an incompatible data volume blindly.

## Release rule

Before publishing a package, container, binary, generated product, or other redistribution, verify the exact shipped versions and preserve all required copyright, license, NOTICE, source-offer, or reciprocal-license obligations for those artifacts. `docs/03_OSS_INTAKE_POLICY.md` remains authoritative for new third-party intake.
