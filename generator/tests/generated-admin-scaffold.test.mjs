import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const manifestPath = join(generatorRoot, "manifests", "admin-auth-proof.json");

function runGenerator(output) {
  return spawnSync(
    process.execPath,
    [generatorPath, "--manifest", manifestPath, "--output", output],
    { encoding: "utf8" },
  );
}

async function snapshot(root) {
  const entries = (await readdir(root, { recursive: true, withFileTypes: true }))
    .filter((entry) => entry.isFile())
    .map((entry) => join(entry.parentPath, entry.name))
    .sort();
  const result = {};
  for (const path of entries) {
    result[relative(root, path)] = await readFile(path, "utf8");
  }
  return result;
}

test("Admin proof emits a deterministic Next.js auth scaffold", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-admin-scaffold-"));
  try {
    const first = join(root, "first");
    const second = join(root, "second");
    const firstRun = runGenerator(first);
    const secondRun = runGenerator(second);
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.deepEqual(await snapshot(first), await snapshot(second));

    const packageJson = JSON.parse(
      await readFile(join(first, "package.json"), "utf8"),
    );
    assert.equal(packageJson.name, "@devforge-proof/generated-admin-proof");
    assert.equal(packageJson.private, true);
    assert.equal(packageJson.scripts.test, "node --test test/*.test.mjs");

    const page = await readFile(join(first, "app", "page.tsx"), "utf8");
    assert.match(page, /<h1>Generated Admin Proof<\/h1>/);
    assert.match(page, /Generated DevForge web authentication product proof/);

    for (const path of [
      "app/api/auth/register/route.ts",
      "app/api/auth/login/route.ts",
      "app/api/auth/me/route.ts",
      "app/api/auth/logout/route.ts",
    ]) {
      const source = await readFile(join(first, path), "utf8");
      assert.ok(source.length > 0, `${path} must not be empty`);
    }

    const generation = JSON.parse(
      await readFile(join(first, ".devforge-generation.json"), "utf8"),
    );
    assert.equal(generation.blueprint, "web-next-auth");
    assert.deepEqual(generation.product, {
      slug: "generated-admin-proof",
      display_name: "Generated Admin Proof",
      package_name: "@devforge-proof/generated-admin-proof",
    });
    assert.deepEqual(generation.modules, ["web-bff-core", "web-session-core"]);
    assert.equal(generation.dependency_mode, "manifest-specs");

    const workflow = await readFile(
      join(first, ".github", "workflows", "ci.yml"),
      "utf8",
    );
    assert.match(workflow, /run: npm run typecheck/);
    assert.match(workflow, /run: npm run build/);
    assert.doesNotMatch(
      workflow,
      /workflow_dispatch|environment:|deploy|release|staging|production/i,
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
