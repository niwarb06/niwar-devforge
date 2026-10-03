import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");

function runGenerator(output) {
  return spawnSync(
    process.execPath,
    [
      generatorPath,
      "--manifest",
      join(generatorRoot, "manifests", "web-auth-proof.json"),
      "--output",
      output,
    ],
    { encoding: "utf8" },
  );
}

test("Web blueprint emits and executes its dependency-free test skeleton", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generated-web-test-"));
  try {
    const output = join(root, "output");
    const generated = runGenerator(output);
    assert.equal(generated.status, 0, generated.stderr);

    const packageJson = JSON.parse(
      await readFile(join(output, "package.json"), "utf8"),
    );
    assert.equal(packageJson.scripts.test, "node --test test/*.test.mjs");

    const skeletonPath = join(output, "test", "scaffold.test.mjs");
    const skeleton = await readFile(skeletonPath, "utf8");
    assert.match(skeleton, /from 'node:test'/);
    assert.doesNotMatch(skeleton, /\{\{[A-Z0-9_]+\}\}/);

    const executed = spawnSync(
      process.execPath,
      ["--test", skeletonPath],
      { cwd: output, encoding: "utf8" },
    );
    assert.equal(executed.status, 0, executed.stderr || executed.stdout);

    const workflow = await readFile(
      join(output, ".github", "workflows", "test.yml"),
      "utf8",
    );
    assert.match(workflow, /^name: Test\n/);
    assert.match(
      workflow,
      /actions\/setup-node@820762786026740c76f36085b0efc47a31fe5020/,
    );
    assert.match(workflow, /node-version: "24\.19\.0"/);
    assert.match(workflow, /run: npm test/);
    assert.doesNotMatch(
      workflow,
      /workflow_dispatch|environment:|secrets\.|deploy|release|staging|production/i,
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
