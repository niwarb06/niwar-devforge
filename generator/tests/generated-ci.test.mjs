import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");

function generate(manifestName, output) {
  return spawnSync(
    process.execPath,
    [
      generatorPath,
      "--manifest",
      join(generatorRoot, "manifests", manifestName),
      "--output",
      output,
    ],
    { encoding: "utf8" },
  );
}

async function generatedWorkflow(manifestName) {
  const root = await mkdtemp(join(tmpdir(), "devforge-generated-ci-"));
  const output = join(root, "output");
  try {
    const run = generate(manifestName, output);
    assert.equal(run.status, 0, run.stderr);
    return await readFile(join(output, ".github", "workflows", "ci.yml"), "utf8");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

function assertNoDeploymentBehavior(workflow) {
  assert.doesNotMatch(workflow, /\bdeploy(?:ment)?\b/i);
  assert.doesNotMatch(workflow, /\bpublish\b/i);
  assert.doesNotMatch(workflow, /\brelease\b/i);
  assert.doesNotMatch(workflow, /secrets\./i);
}

test("Web blueprint emits a pinned build-only CI workflow", async () => {
  const workflow = await generatedWorkflow("web-auth-proof.json");
  assert.match(workflow, /^name: Generated Web CI$/m);
  assert.match(
    workflow,
    /actions\/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1/,
  );
  assert.match(
    workflow,
    /actions\/setup-node@820762786026740c76f36085b0efc47a31fe5020/,
  );
  assert.match(workflow, /node-version: "24"/);
  assert.match(workflow, /npm install --no-audit --no-fund/);
  assert.match(workflow, /npm run typecheck/);
  assert.match(workflow, /npm run build/);
  assertNoDeploymentBehavior(workflow);
});

test("Flutter blueprint emits a pinned analysis and widget-test CI workflow", async () => {
  const workflow = await generatedWorkflow("flutter-auth-proof.json");
  assert.match(workflow, /^name: Generated Flutter CI$/m);
  assert.match(
    workflow,
    /actions\/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1/,
  );
  assert.match(
    workflow,
    /subosito\/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2/,
  );
  assert.match(workflow, /flutter-version: "3\.47\.0"/);
  assert.match(workflow, /flutter pub get/);
  assert.match(workflow, /dart format --output=none --set-exit-if-changed lib test/);
  assert.match(workflow, /flutter analyze/);
  assert.match(workflow, /flutter test test\/auth_screen_test\.dart --reporter expanded/);
  assert.doesNotMatch(workflow, /real_backend_test/);
  assertNoDeploymentBehavior(workflow);
});
