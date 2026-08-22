# Niwar DevForge — Pilot Proof Metrics

Status: **EVIDENCE BASELINE COMPLETE; PHASE 8 REMAINS OPEN**

Evidence date: 2026-08-22

This document records the Phase 8 pilot measurements required by `docs/01_ROADMAP_0_TO_100.md` for two materially different products generated from Niwar DevForge. It deliberately does **not** claim that either pilot is a Production Candidate.

## 1. Evidence snapshot

| Pilot | Platform / boundary | PR | Exact evidence head | Runtime proof |
| --- | --- | --- | --- | --- |
| Generated Web Auth | Next.js browser -> BFF -> FastAPI -> PostgreSQL/Redis | #23 | `1c26aaeea54c0d042ebc87b4986879df7ab6c60f` | Chromium register/login/current-session/logout/post-logout rejection |
| Generated Mobile Auth | Flutter mobile client -> FastAPI -> PostgreSQL/Redis | #24 | `e69c81e2ce128d330286f0dddce160218c514c59` | Flutter widget E2E, Android debug APK host build, real-backend register/login/profile/update/logout |

PR #23: `https://github.com/niwarb06/niwar-devforge/pull/23`

PR #24: `https://github.com/niwarb06/niwar-devforge/pull/24`

These pilots are materially different because the web pilot uses the reviewed browser BFF / secure-cookie boundary, while the mobile pilot uses the reviewed Flutter client / secure-session-vault boundary and produces an Android artifact.

## 2. Measurement rules

### 2.1 Reuse percentage

The roadmap asks for `% reused code/modules`. For this first evidence baseline, DevForge uses a **module-level runtime reuse ratio**, not a line-of-code estimate:

`reused DevForge runtime modules / (reused DevForge runtime modules + generated product shell)`

Infrastructure products such as PostgreSQL, Redis, Chromium, Flutter SDK, and Next.js are not counted as DevForge modules in the numerator or denominator.

The generated product shell is counted once because it is the product-specific assembly layer emitted by the generator. Reusable backend/client/session modules are counted individually.

A second metric, **manual product-code avoidance**, records whether any generated product files had to be manually edited after generation to obtain the passing proof.

### 2.2 Time to first working build

For reproducibility, this is measured from the GitHub PR creation timestamp to the first completed green CI run that proved the generated product through its intended runtime boundary.

This is an observable repository metric. It is not a claim about total human engineering time before the PR was opened.

### 2.3 Time to Production Candidate

A duration is recorded only after the product satisfies `docs/12_DEFINITION_OF_DONE.md` Production Candidate gates. Until then the metric is `OPEN / NOT REACHED` rather than an invented estimate.

### 2.4 Defects / regressions

This counts pilot-blocking defects discovered by the proof loop and fixed before the first full green runtime proof. It also records unresolved exact-head regressions separately.

### 2.5 Custom code required

This counts **manual product-local source changes after deterministic generation**. Work added to DevForge itself (new generator blueprint, reusable module fixes, CI harnesses, documentation) is platform investment and is reported separately rather than mislabeled as per-product custom code.

## 3. Pilot A — Generated Web Auth

### Reused modules

Runtime building blocks:

1. `web-bff-core` — reused DevForge module
2. `web-session-core` — reused DevForge module
3. `backend-core` — reused DevForge backend service
4. generated Next.js product shell — generated assembly layer

**Module-level reuse ratio: 3 / 4 = 75.0%**

The generator manifest directly selects `web-bff-core` and `web-session-core`; the runtime CI proves the generated product against the reusable `backend-core` service.

### Manual product-code avoidance

**100% of the product-local scaffold used by the proof was generator-emitted.**

**Manual post-generation product source files required: 0.**

The proof does require DevForge-owned generator templates and a CI/runtime harness, but no generated product file is patched after generation to make the product pass.

### Time to first working runtime build

- PR #23 created: `2026-08-22T15:26:03Z`
- Exact-head successful Generator Web Auth CI completed: `2026-08-22T15:30:22Z`
- Workflow run: `32581799993`
- Observable PR-open-to-green-runtime duration: **4 minutes 19 seconds**

The successful run proved deterministic double generation, reusable package builds, backend migration/startup, generated product install/typecheck/production build, Chromium startup, register/login/current-session/logout, cookie clearing, and post-logout rejection.

### Defects / regressions

- Pilot-blocking defects recorded in the PR #23 runtime proof loop after the generator slice was available: **0**
- Unresolved exact-head runtime regressions: **0**

This does not mean the wider stacked web work had no earlier engineering defects; it means the measured generated-runtime pilot PR reached its exact-head green proof without a recorded blocking regression in that proof slice.

### Production Candidate metric

**OPEN / NOT REACHED.**

The pilot is a local/CI runtime proof, not a staged product release. Production-candidate duration therefore cannot yet be reported.

Important open gates include real staging deployment, production-like secrets and release controls, deployed ingress/LB/certificate ownership, monitoring/health validation, rollback/backup evidence where applicable, and remaining production security gates.

## 4. Pilot B — Generated Flutter Mobile Auth

### Reused modules

Runtime building blocks:

1. `flutter-auth-core` — reused DevForge module
2. `backend-core` — reused DevForge backend service
3. generated Flutter product shell — generated assembly layer

**Module-level reuse ratio: 2 / 3 = 66.7%**

The generator manifest directly selects `flutter-auth-core`; the runtime CI proves the generated product client against the reusable `backend-core` service.

### Manual product-code avoidance

**100% of the product-local scaffold used by the proof was generator-emitted.**

**Manual post-generation product source files required: 0.**

The pilot required DevForge platform work to add the `flutter-mobile-auth` blueprint and associated CI proof. That work is reusable framework investment, not a one-off patch inside the generated product.

### Time to first working runtime build

- PR #24 created: `2026-08-22T15:41:13Z`
- First full green Generator Flutter Auth CI completed: `2026-08-22T16:22:37Z`
- First full green runtime head: `ba89cdb4a22825ab08eabfacaa19d680a7fcb201`
- Workflow run: `32584120140`
- Observable PR-open-to-first-green-runtime duration: **41 minutes 24 seconds**

A later documentation-only exact head, `e69c81e2ce128d330286f0dddce160218c514c59`, repeated all relevant gates successfully in workflow run `32584193945`, completed at `2026-08-22T16:23:51Z`.

The final exact-head proof passed generator tests, reusable Flutter auth-core validation, backend migrations, byte-identical double generation, dependency resolution, formatting, analyzer, widget E2E, Android debug APK host build, backend startup, and generated Flutter real-backend auth E2E.

### Defects / regressions

Pilot-blocking defects discovered and fixed before the first full green runtime proof: **2**

1. **Scrollable widget viewport interaction** — authenticated `Update profile` / `Logout` controls could be outside the widget-test viewport, so direct taps did not execute the intended action. The test was hardened with explicit visibility handling before interaction.
2. **Android SDK compatibility** — `flutter_secure_storage 11.0.0` required Android compile SDK 37 while the pinned Flutter 3.47 proof toolchain generated an Android SDK 36 host. The reviewed compatibility pin was changed to `flutter_secure_storage 10.3.1`, preserving platform secure storage while restoring the supported toolchain boundary. Module and third-party review documentation were updated.

Unresolved exact-head CI regressions: **0**.

### Production Candidate metric

**OPEN / NOT REACHED.**

The current proof builds an Android debug APK in CI but does not yet satisfy the Production Candidate definition. Important open gates include real Android/iOS device or emulator secure-storage integration, iOS artifact/device proof, staging deployment, release security/dependency/secret gates, monitoring/health validation, and rollback/release evidence.

## 5. Combined Phase 8 metrics

| Metric | Generated Web Auth | Generated Flutter Mobile Auth | Combined observation |
| --- | ---: | ---: | --- |
| Module-level reuse | 75.0% | 66.7% | **5 reused modules / 7 counted runtime building blocks = 71.4%** |
| Manual product-code avoidance | 100% | 100% | **0 post-generation product source edits in both pilots** |
| Time to first working runtime build | 4m 19s | 41m 24s | Both measured from PR-open to first full green runtime proof |
| Pilot-blocking defects found/fixed | 0 | 2 | **2 total; 0 unresolved exact-head regressions** |
| Time to Production Candidate | OPEN | OPEN | **Not yet measurable as a duration** |

## 6. What the evidence proves

The two pilots prove that DevForge can deterministically assemble and validate two materially different product surfaces from reusable modules:

- a browser product using a BFF / HttpOnly-cookie security model; and
- a Flutter mobile product using a secure local session vault and mobile API-client security model.

Both generated products run against the same reusable FastAPI backend with PostgreSQL and Redis. Both exact-head proof lines are green, and the mobile pilot additionally proves Android APK host compilation.

The evidence also shows that failures found by the pilot loop were repaired in reusable DevForge boundaries rather than patched into generated product output.

## 7. Why Phase 8 remains open

`docs/12_DEFINITION_OF_DONE.md` requires repository evidence for a phase to be Done and defines additional gates for a Production Candidate. `docs/04_SECURITY_BASELINE.md` also requires staging before production, reproducible controlled builds, rollback capability, tested backups where applicable, and release security controls.

Because neither pilot has reached that production-candidate state, the required `time to production candidate` metric has no valid duration yet.

Therefore:

- **Two materially different pilots:** PASS
- **Reuse measurement:** PASS
- **First-working-build measurement:** PASS
- **Defect/regression measurement:** PASS
- **Custom-code measurement:** PASS
- **Production-candidate duration:** OPEN
- **Phase 8 / 100% completion claim:** **NOT YET APPROVED**

## 8. Next proof gate

The next evidence-bearing step should take one pilot through a real staging / production-candidate path without weakening existing gates. The smaller next target is the web pilot because its production-like TLS ingress behavior is already separately proven in the stacked web work.

Minimum next evidence should include:

- deployed staging environment with real TLS/certificate ownership;
- explicit trusted-proxy/network topology and service isolation;
- controlled staging secrets with secret/dependency/security checks;
- health/monitoring evidence;
- rollback procedure and applicable backup/restore evidence;
- release notes and a recorded Production Candidate timestamp;
- no production deployment without explicit human approval.

Once the first pilot reaches Production Candidate, record its duration here. Phase 8 should only be considered fully complete after the remaining roadmap/Definition-of-Done interpretation is reviewed against that evidence.