# Niwar DevForge — Reusable Module Contract

Every reusable module must satisfy this contract before it is promoted into the DevForge catalog.

## Required Metadata
Each module documents:
- `name`
- `version`
- `status`: experimental | beta | stable | deprecated
- `owners`
- `supported_targets`: mobile | web | admin | backend | worker
- `dependencies`
- `configuration`
- `public interfaces`
- `events/webhooks`
- `data models/migrations`
- `permissions`
- `security considerations`
- `tests`
- `upgrade notes`

## Design Rules
1. Product-specific branding, secrets, IDs, domains, and business names must not exist in reusable code.
2. External providers sit behind interfaces/adapters when a realistic alternative provider may be needed later.
3. Cross-module dependencies must be explicit and minimal.
4. Modules own their domain logic; callers use public contracts rather than internal implementation details.
5. Database changes are migration-driven and backward-compatible when practical.
6. User-facing strings are localizable from the start.
7. RTL/LTR behavior must be supported where the module has UI.
8. Accessibility and loading/error/empty states are part of the module, not afterthoughts.

## Minimum Quality Gate
A stable module requires:
- unit tests for domain logic;
- integration tests for external/data boundaries where applicable;
- documented happy path and failure behavior;
- no known Critical/High security issue;
- no committed secret;
- license-clear dependencies;
- versioned migration/API compatibility notes;
- at least one successful use in a pilot or production-like environment.

## Versioning
Use semantic versioning for reusable modules:
- MAJOR: incompatible public contract/data behavior
- MINOR: backward-compatible features
- PATCH: backward-compatible fixes

## Provider Adapter Pattern
Examples of provider-independent domains:
- payments
- notifications
- storage
- maps/geocoding
- identity verification
- email/SMS/OTP
- AI model providers

Product packs select an adapter through configuration rather than embedding provider-specific logic throughout the codebase.

## Promotion Flow
`experimental` → audit → tests → pilot use → documentation → `beta` → repeated use → `stable`.

Code must not be promoted only because it worked once in one product.
