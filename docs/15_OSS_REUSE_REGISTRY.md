# Niwar DevForge — High-Value OSS Reuse Registry

Snapshot: 2026-09-29

## Purpose

Record high-value public repositories that can materially reduce implementation time for the remaining DevForge roadmap while preserving the existing provider-neutral architecture, OSS intake policy, security baseline, and no-blind-copy rule.

This registry is a pre-integration decision record. **No third-party source code is vendored or imported by this document.** Before any candidate becomes a runtime dependency or copied/adapted implementation, DevForge must pin an exact release/tag/commit, re-check license/security/dependencies/tests, preserve required notices, and pass the repository quality gates.

## Decision labels

- **ADOPT CANDIDATE** — strong fit for direct tool/library use after an integration-specific verification PR.
- **ADAPT** — use behind a DevForge contract/adapter; do not couple reusable domain code to the candidate.
- **REFERENCE** — use architecture, domain modeling, tests, or workflow ideas; do not directly import the application/core implementation.
- **ALTERNATIVE** — keep as a reviewed fallback, not as a second default framework.

Scores below are **pre-integration scores**, not final trust scores. They summarize current functional fit, license, maintenance, architecture fit, documentation, and expected reuse value. Security-sensitive areas still require a focused implementation audit.

## Tier A — highest expected time savings

| Repository | Roadmap fit | License observed | Decision | Pre-score | Why it matters / boundary |
| --- | --- | --- | --- | ---: | --- |
| `copier-org/copier` | Phase 5 Generator | MIT | **ADOPT CANDIDATE** | 92 | Python template engine/CLI with Git/local templates, questionnaires, project generation/update behavior, CI and typing evidence. Strong match for deterministic DevForge scaffolding. Integrate only through a pinned generator dependency; DevForge remains owner of templates/contracts/output validation. |
| `formancehq/ledger` | Phase 3 Wallet ledger abstraction | MIT | **ADAPT** | 88 | Purpose-built programmable financial ledger with atomic multi-posting transactions and PostgreSQL storage. Use as a ledger-semantics/reference or optional external ledger adapter; do not make DevForge wallet contracts depend on its DSL/API. |
| `tus/tusd` | Phase 3 Media / Storage uploads | MIT | **ADAPT** | 89 | Mature reference server for the open resumable-upload protocol. Valuable for large/mobile media uploads and retry/resume behavior. Prefer protocol/adapter integration rather than embedding its Go server in core packages. |
| `imgproxy/imgproxy` | Phase 3 Media | Apache-2.0 | **ADAPT** | 88 | Dedicated image resize/process/convert service with active maintenance. Strong optional media-processing adapter; keep transformation policy and authorization in DevForge, not in provider-specific code. |
| `openai/openai-agents-python` | Phase 6 AI Agent Automation | MIT | **ADOPT CANDIDATE** | 92 | Python multi-agent framework with tools, guardrails, handoffs, human-in-the-loop, sessions, tracing, sandbox agents and provider-agnostic model support. Strong fit with the FastAPI/Python stack. Integrate behind DevForge agent/model boundaries and retain human approval rules. |
| `aquasecurity/trivy` | Phase 7 Security / QA / CI-CD | Apache-2.0 | **ADOPT CANDIDATE** | 94 | Consolidates vulnerability, misconfiguration, secret and SBOM scanning across repositories/containers/IaC. Add only after designing a pinned, fail-closed CI policy that does not duplicate existing gates unnecessarily. |
| `gitleaks/gitleaks` | Phase 7 Security / QA / CI-CD | MIT | **ADOPT CANDIDATE** | 93 | Focused secret scanning with mature CI/CD usage. Candidate for a pinned PR/CI secret gate; repository-specific allowlists must be explicit and reviewed. |
| `ossf/scorecard` | Phase 1 OSS audit + Phase 7 supply chain | Apache-2.0 | **ADOPT CANDIDATE** | 89 | Security-health assessment for open-source dependencies/sources. Useful to strengthen DevForge OSS intake evidence before adopting future repositories; treat score as evidence, not an automatic accept/reject decision. |

## Tier B — strong reference / optional adapters

| Repository | Roadmap fit | License observed | Decision | Pre-score | Why it matters / boundary |
| --- | --- | --- | --- | ---: | --- |
| `killbill/killbill` | Phase 3 Payments + Subscriptions | Apache-2.0 | **REFERENCE** | 84 | Long-lived modular subscription billing/payment platform. Reuse billing-state, entitlement, invoice, payment, retry and plugin-boundary ideas. Do **not** copy payment/security-sensitive implementation blindly; language/runtime also differs from DevForge. |
| `medusajs/medusa` | Phase 4 Marketplace / Commerce | MIT for non-Enterprise materials; separate Enterprise license exists | **REFERENCE / SELECTIVE ADAPT** | 82 | Large active commerce platform with rich commerce workflows. Useful for catalog/order/cart/inventory/payment-provider domain ideas. Explicitly exclude Enterprise-licensed materials and avoid importing the whole framework into the DevForge core. |
| `livekit/livekit` | Phase 3 Chat/realtime + Media; AI/SaaS pack | Apache-2.0 | **ADAPT** | 84 | Mature realtime WebRTC/media stack. Candidate optional adapter for voice/video/realtime products; avoid coupling the base chat/realtime contract to LiveKit-specific semantics. |
| `Project-OSRM/osrm-backend` | Phase 4 Delivery/logistics + Maps | BSD-2-Clause | **ADAPT** | 85 | Mature OpenStreetMap routing engine with routing/map-matching/isochrone capabilities. Treat as an optional routing provider behind DevForge maps/logistics adapters, not as core domain code. |
| `openwallet-foundation/credo-ts` | Phase 3 Verification/KYC abstraction | Apache-2.0 | **REFERENCE** | 76 | Useful standards-oriented reference for decentralized identity, DID, OpenID4VC and verifiable credentials. It is not a complete KYC solution; use only to inform portable verification/credential interfaces where relevant. |
| `pydantic/pydantic-ai` | Phase 6 AI Agent Automation / AI-SaaS | MIT | **ALTERNATIVE** | 85 | Typed Python agent framework closely aligned with the backend stack. Keep as a reviewed alternative/reference; do not default to two competing agent frameworks unless a later benchmark justifies it. |

## Integration order tied to the current roadmap

1. **Current Phase 3 — Payments/Subscriptions:** use Kill Bill as a reference for state machines, retries, invoicing boundaries, entitlement and provider/plugin separation; keep DevForge contracts provider-neutral.
2. **Current Phase 3 — Wallet ledger:** use Formance Ledger to validate double-entry/atomic-posting semantics and adapter requirements; no direct financial-state dependency without a focused security/data-model review.
3. **Current Phase 3 — Media:** use tus concepts for resumable uploads and imgproxy as an optional processing-service adapter. LiveKit remains optional for realtime voice/video products.
4. **Phase 4 — Product packs:** use Medusa selectively for commerce-domain reference and OSRM behind the delivery/logistics routing adapter. Do not import product branding or Enterprise-licensed Medusa materials.
5. **Phase 5 — Generator:** evaluate pinned Copier integration as the primary template-rendering engine instead of rebuilding template update/render behavior from scratch.
6. **Phase 6 — Agents:** benchmark a pinned OpenAI Agents SDK integration against DevForge requirements. Keep PydanticAI as the typed alternative; choose one default rather than creating framework sprawl.
7. **Phase 7 — Security:** evaluate pinned Trivy + Gitleaks gates and OpenSSF Scorecard intake evidence, preserving current CodeQL/supply-chain checks and avoiding redundant CI noise.

## Explicitly not approved by this registry

- No automatic vendoring, subtree/submodule import, or bulk copying.
- No new runtime dependency is approved merely because it appears in this list.
- No payment, wallet, KYC, auth, cryptography, or security-sensitive code may bypass focused review.
- No GPL/AGPL/network-copyleft candidate is approved here for DevForge reusable commercial foundations.
- No provider credential, product-specific identifier, customer data, branding, or proprietary/Enterprise material may enter reusable packages.
- No VPS, staging, release, deployment, or production action is authorized by this registry.

## Evidence snapshot

At the time of this review, the shortlisted repositories were public, non-archived, recently maintained, and their observed licenses matched the entries above. `medusajs/medusa` requires special care because its root license states that non-Enterprise materials are MIT while identified Enterprise Edition materials are governed separately.

Before integration, the implementation PR must add the exact release/tag/commit used plus any required copyright/license notices and record the final DevForge audit score/decision.