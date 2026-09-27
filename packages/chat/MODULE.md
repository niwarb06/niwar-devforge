# Chat Module

- Name: chat
- Version: 0.1.0
- Status: EXPERIMENTAL
- Owner: Niwar DevForge
- Targets: mobile, web, admin, backend, worker

## Purpose

Provides the first provider-neutral Phase-3 chat/realtime contract for Niwar DevForge. This foundation slice establishes realtime-event capability and a strict provider-adapter boundary. Message persistence, conversations, delivery/read state, presence, attachments, moderation behavior, and product-specific chat UX are intentionally out of scope.

## Dependencies

None at runtime. The repository validator and tests use only the Python standard library.

## Configuration

`chat-contract.json` is the source of truth for this experimental contract.

## Public Interfaces

- `chat-contract.json` — versioned chat/realtime capability metadata.
- `validate_chat_contract.py` — fail-closed repository validator.

Consumers must treat realtime transport as an adapter boundary rather than embedding provider-specific transport behavior into reusable product logic.

## Events / Webhooks

This slice defines only the existence of a `realtime_events` capability. Event schemas, transport protocols, subscriptions, delivery guarantees, and webhook behavior are not defined here.

## Data Models / Migrations

None.

## Permissions

None in this foundation slice. Future messaging or conversation permissions require separate approval and implementation.

## Security Considerations

- Provider credentials and secrets must never be committed to this package.
- Realtime transport must not bypass authentication, authorization, tenant isolation, or audit requirements.
- Product-specific identifiers, domains, customer data, and message content must not be part of this reusable capability contract.
- Provider-specific code belongs behind an adapter boundary.

## Tests

`tests/test_validate_chat_contract.py` proves:
- the committed contract is valid;
- the domain is `chat`;
- the baseline capability is exactly `realtime_events`;
- a provider adapter is required;
- extra or malformed baseline capability values fail validation;
- unknown contract keys fail validation.

Path-scoped GitHub Actions CI runs the validator and unit tests without adding third-party dependencies.

## Upgrade Notes

Changing the domain, baseline capability, adapter requirement, or schema version is a public-contract change and requires compatibility review for downstream modules and generated products.

The module remains EXPERIMENTAL until chat/messaging behavior, event schemas, provider integration, generated-product integration, and security tests are separately approved and proven.
