# Phase 1 — Open Source Candidate Shortlist

Status: INITIAL SHORTLIST ONLY. No code imported yet.

## Candidate A — Vinta Next.js + FastAPI Template
Repository: `vintasoftware/nextjs-fastapi-template`
License: MIT

### Why it is interesting
- FastAPI + Next.js + TypeScript alignment with DevForge defaults
- End-to-end type safety via generated OpenAPI client
- Zod validation
- Authentication foundation
- Docker Compose
- CI and coverage signals
- pre-commit automation

### Potential DevForge value
- API contract generation pattern
- typed frontend client workflow
- auth architecture reference
- project/bootstrap conventions
- Docker/CI conventions

### Risks / required audit
- do not copy wholesale;
- verify current dependency health and maintenance;
- inspect auth implementation and deployment assumptions;
- Vercel/serverless choices may not match DevForge provider-neutral baseline;
- preserve MIT copyright/license notice for any substantial copied portions.

Initial state: CANDIDATE

---

## Candidate B — bizz84 Flutter Riverpod Reference Architecture
Repository: `bizz84/starter_architecture_flutter_firebase`
License: MIT

### Why it is interesting
- feature-oriented Flutter reference architecture;
- Riverpod-based dependency/data-state architecture;
- GoRouter navigation;
- authentication and CRUD reference flow;
- repository pattern documentation;
- multi-device synced data example.

### Potential DevForge value
- Flutter feature-first organization;
- repository/service boundary ideas;
- navigation architecture;
- initialization patterns;
- testable state-management conventions.

### Risks / required audit
- repository explicitly describes itself as low-priority maintenance;
- roadmap still lists missing tests, localization, responsive UI, and consistency work;
- Firebase-specific implementation must not become DevForge core lock-in;
- use architecture ideas selectively, not the whole application.

Initial state: CANDIDATE / REFERENCE_ONLY

---

## Candidate C — meetqy Flutter Dating Template
Repository: `meetqy/flutter_dating_template`
Previously reviewed license: MIT.

### Why it is interesting
- broad dating/social screen coverage;
- fast visual reference for a future dating product pack.

### Required restriction
This is not a DevForge core architecture candidate. It may only be used as a visual/feature reference after validating design/prototype rights and modernizing dependencies. Product/domain UI must be rebuilt within DevForge standards rather than copied blindly.

Initial state: REFERENCE_ONLY

---

## Category Discovery Pool — Not Approved
Search discovery also found booking, marketplace, and delivery Flutter repositories. These remain UNREVIEWED and must not be imported merely because they match a category name.

Examples for later audits:
- `sangvaleap/app-flutter-hotel-booking`
- `tranphong9mx/flutter_booking_app`
- `Frave07/Flutter-Delivery-App`
- `lambiengcode/flutter-web-marketplace`

State: UNREVIEWED

## OSS Intake Rule for Phase 1
For each candidate:
1. confirm license from repository source;
2. inspect recent maintenance/commit activity;
3. inspect dependency freshness;
4. inspect secrets/credentials and unsafe defaults;
5. inspect auth/data authorization boundaries;
6. inspect test quality and CI;
7. score with DevForge audit scorecard;
8. decide one of: REJECT, REFERENCE_ONLY, EXTRACT_PATTERN, VENDOR_COMPONENT;
9. record license obligations before any code enters DevForge.
