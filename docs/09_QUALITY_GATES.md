# Niwar DevForge — Quality Gates

Every reusable module and every production candidate must pass the gates that apply to its risk level.

## Gate A — Build and Static Quality
- Clean dependency install
- Formatting/lint passes
- Type checking passes
- Build succeeds
- No committed secrets

## Gate B — Tests
- Unit tests for business logic
- Integration tests for persistence/provider boundaries
- End-to-end tests for critical user journeys
- Regression tests for fixed defects

## Gate C — Security
- Authorization paths tested server-side
- Dependency vulnerability scan reviewed
- Secret scan passes
- Upload, webhook, payment, admin, and authentication surfaces tested where applicable
- No unexplained cleartext production transport

## Gate D — Data and Migrations
- Migration is forward-safe
- Destructive changes have explicit approval, backup, and rollback strategy
- Seed/test data cannot mutate production data
- Tenant/workspace boundaries verified where applicable

## Gate E — Product Quality
- Loading, empty, success, and failure states handled
- Localization checked for ku/ar/en where the product supports all three
- RTL/LTR behavior validated
- Accessibility basics checked
- Mobile responsive states checked where applicable

## Gate F — Operations
- Environment configuration documented
- Health/readiness checks available where appropriate
- Logging/monitoring configured
- Staging validation complete
- Rollback procedure defined

## Gate G — Reusability (DevForge modules only)
A module cannot enter the trusted catalog until it is:
- product-neutral;
- documented;
- versioned;
- tested independently;
- free of product secrets/branding/data;
- clear about required adapters and configuration.

## Severity Rule
Known Critical or exploitable High-risk defects block production. Medium/Low findings require an explicit tracked disposition when not fixed immediately.
