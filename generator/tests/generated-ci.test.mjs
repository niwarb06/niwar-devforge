import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");

function runGenerator(manifestName, output) {
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
  try {
    const output = join(root, "output");
    const run = runGenerator(manifestName, output);
    assert.equal(run.status, 0, run.stderr);
    return await readFile(join(output, ".github", "workflows", "ci.yml"), "utf8");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("web blueprint emits its deterministic generated CI contract", async () => {
  const workflow = await generatedWorkflow("web-auth-proof.json");

  assert.match(workflow, /^name: CI\n/);
  assert.match(workflow, /actions\/setup-node@820762786026740c76f36085b0efc47a31fe5020/);
  assert.match(workflow, /node-version: "24\.19\.0"/);
  assert.match(workflow, /run: npm install --no-audit --no-fund/);
  assert.match(workflow, /run: npm run typecheck/);
  assert.match(workflow, /run: npm run build/);
  assert.match(workflow, /DEVFORGE_PRODUCT_PUBLIC_ORIGIN: https:\/\/app\.example\.test/);
  assert.match(workflow, /DEVFORGE_PRODUCT_BACKEND_API_BASE_URL: https:\/\/api\.example\.test\/api\/v1/);
  assert.doesNotMatch(workflow, /flutter pub get|flutter analyze|flutter test/);
  assert.doesNotMatch(workflow, /workflow_dispatch|environment:|deploy|release|staging/i);
});

test("Flutter blueprint emits its deterministic generated CI contract", async () => {
  const workflow = await generatedWorkflow("flutter-auth-proof.json");

  assert.match(workflow, /^name: CI\n/);
  assert.match(workflow, /subosito\/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2/);
  assert.match(workflow, /flutter-version: "3\.47\.0"/);
  assert.match(workflow, /run: flutter pub get/);
  assert.match(workflow, /run: dart format --output=none --set-exit-if-changed lib test/);
  assert.match(workflow, /run: flutter analyze/);
  assert.match(workflow, /run: flutter test/);
  assert.doesNotMatch(workflow, /npm run typecheck|npm run build|actions\/setup-node/);
  assert.doesNotMatch(workflow, /workflow_dispatch|environment:|deploy|release|staging/i);
});
