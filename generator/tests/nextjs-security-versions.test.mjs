import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../", import.meta.url);
const readText = (path) => readFileSync(new URL(path, root), "utf8");
const readJson = (path) => JSON.parse(readText(path));

// Reviewed exact pins; superseded or future, unreviewed minor/major releases
// must not silently pass the security gate. Vendor releases: 2026-10-14
// (GHSA-2464-fhr4-w9xw, GHSA-p3m5-59mp-jv5r), 2026-11-03
// (GHSA-pc58-hwjq-p385, GHSA-7qx7-33qx-rqx2, GHSA-f3mh-rxg3-f5g2,
// and 16.x cache advisories). Any future change requires test review.
const APPROVED_NEXT = Object.freeze({
  webPilot: "15.5.29",
  generatedWebAndAdmin: "16.4.5",
});

function assertApprovedPatchedNext(version, approvedVersion) {
  assert.match(version, /^\d+\.\d+\.\d+$/, "pin a fully qualified Next.js release");
  assert.equal(
    version,
    approvedVersion,
    `Next.js ${version} is not the independently reviewable approved security pin ${approvedVersion}`,
  );
}

test("generated Web and Admin pin the reviewed November 2026 security release", () => {
  const files = readJson("generator/templates/web-next-auth/files.json");
  const pkg = JSON.parse(files["package.json"]);
  assertApprovedPatchedNext(pkg.dependencies.next, APPROVED_NEXT.generatedWebAndAdmin);
});

test("Web pilot pins the reviewed November 2026 security release", () => {
  const pkg = readJson("apps/web_next/package.json");
  assertApprovedPatchedNext(pkg.dependencies.next, APPROVED_NEXT.webPilot);
});

test("security guard rejects prior vulnerable and unreviewed pins", () => {
  for (const [version, expected] of [
    ["15.5.24", APPROVED_NEXT.webPilot],
    ["15.5.28", APPROVED_NEXT.webPilot],
    ["15.5.30", APPROVED_NEXT.webPilot],
    ["15.6.0", APPROVED_NEXT.webPilot],
    ["16.4.3", APPROVED_NEXT.generatedWebAndAdmin],
    ["16.4.4", APPROVED_NEXT.generatedWebAndAdmin],
    ["16.4.6", APPROVED_NEXT.generatedWebAndAdmin],
    ["16.5.0", APPROVED_NEXT.generatedWebAndAdmin],
    ["17.0.0", APPROVED_NEXT.generatedWebAndAdmin],
    ["^16.4.5", APPROVED_NEXT.generatedWebAndAdmin],
  ]) {
    assert.throws(
      () => assertApprovedPatchedNext(version, expected),
      /fully qualified Next\.js release|not the independently reviewable approved security pin/,
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
