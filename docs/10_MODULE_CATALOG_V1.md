# Niwar DevForge — Module Catalog V1

## Foundation Modules
- config
- secrets-interface
- logging
- error-model
- localization
- design-tokens
- API contracts/client
- database/migrations
- audit events
- feature flags

## Identity and Access
- authentication
- OTP
- sessions
- users/profiles
- roles/permissions
- tenant/workspace membership
- account recovery
- account deletion

## Communication
- push notifications
- email adapter
- SMS/OTP adapter
- realtime events
- chat/messaging
- media messages

## Media and Storage
- file upload
- image processing
- video upload
- private/signed access
- storage provider adapter

## Discovery
- search
- filters
- pagination
- favorites
- reviews/ratings
- recommendations interface

## Location
- maps adapter
- geocoding
- current location
- distance/search radius
- live tracking interface

## Commerce
- payments adapter
- webhook processing
- refunds interface
- subscriptions
- coupons/promotions
- wallet/ledger
- invoices/receipts

## Trust and Safety
- block/report
- moderation workflow
- KYC/identity adapter
- device/risk signals interface
- abuse rate limits
- admin audit trail

## Product Packs

### Business Pack
CRUD, dashboards, reports, roles, export/import.

### Booking Pack
Listings/properties, availability calendar, reservations, cancellation rules, host/owner workflows.

### Marketplace Pack
Products, sellers, cart, checkout, orders, fulfillment.

### Dating/Social Pack
Profiles, discovery, swipe/action model, match state, chat, privacy, safety.

### Delivery/Logistics Pack
Orders, driver/courier state, assignment, route/location, proof of delivery.

### AI/SaaS Pack
Workspaces, usage/metering, model/provider adapter, prompt/job history, billing hooks.

## Catalog States
Each module is one of:
- IDEA
- CANDIDATE
- EXPERIMENTAL
- TRUSTED
- DEPRECATED

Only TRUSTED modules are used by default in production generators.
