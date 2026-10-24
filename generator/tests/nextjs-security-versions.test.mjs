import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const root = new URL("../../", import.meta.url);
const readText = (path) => readFileSync(new URL(path, root), "utf8");
const readJson = (path) => JSON.parse(readText(path));

function assertSecurityPatchedNext(version) {
  assert.match(version, /^\d+\.\d+\.\d+$/, "pin a fully qualified Next.js release");
  const [major, minor, patch] = version.split(".").map(Number);
  // October 14, 2026 vendor advisory: GHSA-2464-fhr4-w9xw and
  // GHSA-p3m5-59mp-jv5r. Future major versions require explicit review.
  const patched =
    (major === 15 && (minor > 5 || (minor === 5 && patch >= 28))) ||
    (major === 16 && (minor > 4 || (minor === 4 && patch >= 1)));
  assert.ok(patched, `Next.js ${version} is not a verified patched release`);
}

test("generated Web and Admin use an October 2026 security-patched Next.js", () => {
  const files = readJson("generator/templates/web-next-auth/files.json");
  const pkg = JSON.parse(files["package.json"]);
  assertSecurityPatchedNext(pkg.dependencies.next);
});

test("Web pilot uses an October 2026 security-patched Next.js", () => {
  const pkg = readJson("apps/web_next/package.json");
  assertSecurityPatchedNext(pkg.dependencies.next);
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
