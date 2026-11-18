import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../", import.meta.url);
const readText = (path) => readFileSync(new URL(path, root), "utf8");
const readJson = (path) => JSON.parse(readText(path));

// Candidate exact pins; independent human review is still required. Older or
// future, unreviewed minor/major releases must not pass. Vendor: 2026-10-14
// (GHSA-2464-fhr4-w9xw, GHSA-p3m5-59mp-jv5r), 2026-11-03
// (GHSA-pc58-hwjq-p385, GHSA-7qx7-33qx-rqx2, GHSA-f3mh-rxg3-f5g2,
// and 16.x cache advisories). Any future change requires test review.
const TARGET_NEXT = Object.freeze({
  webPilot: "15.5.29",
  generatedWebAndAdmin: "16.4.5",
});

function assertTargetSecurityPin(version, targetVersion) {
  assert.match(version, /^\d+\.\d+\.\d+$/, "pin a fully qualified Next.js release");
  assert.equal(
    version,
    targetVersion,
    `Next.js ${version} is not the expected November 2026 security pin ${targetVersion}`,
  );
}

test("generated Web and Admin pin the November 2026 candidate security release", () => {
  const files = readJson("generator/templates/web-next-auth/files.json");
  const pkg = JSON.parse(files["package.json"]);
  assertTargetSecurityPin(pkg.dependencies.next, TARGET_NEXT.generatedWebAndAdmin);
});

test("Web pilot pins the November 2026 candidate security release", () => {
  const pkg = readJson("apps/web_next/package.json");
  assertTargetSecurityPin(pkg.dependencies.next, TARGET_NEXT.webPilot);
});

test("security guard rejects prior vulnerable and unreviewed pins", () => {
  for (const [version, expected] of [
    ["15.5.24", TARGET_NEXT.webPilot],
    ["15.5.28", TARGET_NEXT.webPilot],
    ["15.5.30", TARGET_NEXT.webPilot],
    ["15.6.0", TARGET_NEXT.webPilot],
    ["16.4.3", TARGET_NEXT.generatedWebAndAdmin],
    ["16.4.4", TARGET_NEXT.generatedWebAndAdmin],
    ["16.4.6", TARGET_NEXT.generatedWebAndAdmin],
    ["16.5.0", TARGET_NEXT.generatedWebAndAdmin],
    ["17.0.0", TARGET_NEXT.generatedWebAndAdmin],
    ["^16.4.5", TARGET_NEXT.generatedWebAndAdmin],
  ]) {
    assert.throws(
      () => assertTargetSecurityPin(version, expected),
      /fully qualified Next\.js release|not the expected November 2026 security pin/,
    );
  }
});

test("standalone and staging npm audit security gates remain enforced", () => {
  for (const path of [
    ".github/workflows/standalone-package-distribution-ci.yml",
    ".github/workflows/generator-admin-auth-ci.yml",
  ]) {
    assert.match(readText(path), /npm audit --audit-level=high/);
  }
  assert.match(
    readText(".github/workflows/web-staging-candidate-ci.yml"),
    /npm audit --omit=dev --audit-level=high/,
  );
});
