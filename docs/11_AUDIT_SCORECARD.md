# Niwar DevForge — Reuse / Open-Source Audit Scorecard

Use this scorecard before importing internal or third-party code into DevForge.

## Hard Gates
Reject or quarantine a candidate if any answer is unacceptable:
- License is missing, unclear, or incompatible with intended use.
- Repository/source provenance is unclear.
- Known secret/private credential is embedded.
- Security model cannot be understood sufficiently for intended reuse.
- Required dependency is abandoned with no realistic replacement path.
- Candidate requires copying protected branding/assets/content we do not have rights to use.

## Weighted Score (100)

### 1. Functional Fit — 20
How much verified useful functionality does it provide for DevForge/product packs?

### 2. Code Quality / Architecture — 15
Separation of concerns, readability, typing, modularity, error handling.

### 3. Security — 15
Auth/authorization, secrets, transport, input validation, dependency risk, sensitive data handling.

### 4. Maintainability — 10
Recent maintenance, understandable codebase, manageable technical debt.

### 5. Test Quality — 10
Useful unit/integration/e2e coverage and reproducible test setup.

### 6. Dependency Health — 10
Current supported frameworks/packages with controlled dependency surface.

### 7. Reusability — 10
Can it be product-neutral, configurable, and isolated behind contracts/adapters?

### 8. Documentation — 5
Setup, architecture, API/module behavior, examples.

### 9. Performance / Scalability — 5
No obvious design that blocks expected product scale.

## Decision Bands
- 85–100: Strong candidate for reuse after verification.
- 70–84: Reuse selected parts after remediation.
- 50–69: Reference/learning value; avoid direct core adoption.
- Below 50: Reject for DevForge core.

## Audit Record
For every candidate record:
- Source repository / internal source
- Commit/tag/version audited
- License
- Last meaningful update
- Score by category
- Security findings
- Selected reusable parts
- Parts explicitly rejected
- Required modernization
- Decision: ADOPT / ADAPT / REFERENCE / REJECT
- Reviewer/date

## Rule
Do not equate GitHub stars, screenshots, or feature count with production quality. Evidence wins.
