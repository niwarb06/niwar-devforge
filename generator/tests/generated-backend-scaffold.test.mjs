import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const manifestPath = join(generatorRoot, "manifests", "backend-auth-proof.json");

function runGenerator(manifest, output) {
  return spawnSync(
    process.execPath,
    [generatorPath, "--manifest", manifest, "--output", output],
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

test("backend blueprint emits a deterministic FastAPI scaffold", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-backend-scaffold-"));
  try {
    const first = join(root, "first");
    const second = join(root, "second");
    const firstRun = runGenerator(manifestPath, first);
    const secondRun = runGenerator(manifestPath, second);
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.deepEqual(await snapshot(first), await snapshot(second));

    assert.equal(
      await readFile(join(first, "requirements.txt"), "utf8"),
      "../../packages/backend-core\n",
    );
    assert.equal(
      await readFile(join(first, "app.py"), "utf8"),
      'from devforge_core.main import app\n\n__all__ = ["app"]\n',
    );

    const env = await readFile(join(first, ".env.example"), "utf8");
    assert.match(env, /^DEVFORGE_APP_NAME=Generated Backend Proof API$/m);
    assert.match(env, /^DEVFORGE_API_PREFIX=\/api\/v1$/m);
    assert.match(env, /^DEVFORGE_DATABASE_URL=postgresql\+psycopg:/m);
    assert.match(env, /^DEVFORGE_REDIS_URL=redis:\/\//m);

    const scaffoldTest = await readFile(
      join(first, "tests", "test_scaffold.py"),
      "utf8",
    );
    assert.match(scaffoldTest, /from devforge_core\.main import app as backend_core_app/);
    assert.match(scaffoldTest, /\/api\/v1\/health\/live/);
    assert.match(scaffoldTest, /\/api\/v1\/auth\/register/);
    assert.match(scaffoldTest, /\/api\/v1\/users\/me/);

    const workflow = await readFile(
      join(first, ".github", "workflows", "ci.yml"),
      "utf8",
    );
    assert.match(workflow, /actions\/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97/);
    assert.match(workflow, /python-version: "3\.12"/);
    assert.match(workflow, /python -m pip install --disable-pip-version-check -r requirements\.txt/);
    assert.match(workflow, /python -m unittest discover -s tests/);
    assert.match(workflow, /python -c "from app import app; assert app"/);
    assert.doesNotMatch(workflow, /workflow_dispatch|environment:|deploy|release|staging|production/i);

    const generation = JSON.parse(
      await readFile(join(first, ".devforge-generation.json"), "utf8"),
    );
    assert.equal(generation.generator_version, "0.4.0");
    assert.equal(generation.blueprint, "backend-fastapi-auth");
    assert.deepEqual(generation.modules, ["backend-core"]);
    assert.deepEqual(generation.package_specs, {
      "backend-core": "../../packages/backend-core",
    });
    assert.equal(generation.dependency_mode, "manifest-specs");

    const compose = await readFile(
      join(first, "infrastructure", "dev", "docker-compose.yml"),
      "utf8",
    );
    assert.match(compose, /image: postgres:16-alpine/);
    assert.match(compose, /image: valkey\/valkey:7\.2\.14-alpine/);

    const migrations = await readdir(join(first, "migrations", "versions"));
    assert.deepEqual(migrations.sort(), [
      "0001_backend_core_baseline.py",
      "0002_identity_sessions.py",
      "0003_roles_tenants.py",
    ]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("backend package path validation fails closed before output", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-backend-path-"));
  try {
    const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
    manifest.package_specs["backend-core"] = "/tmp/backend-core";
    const invalidManifest = join(root, "manifest.json");
    const output = join(root, "output");
    await writeFile(invalidManifest, JSON.stringify(manifest), "utf8");

    const run = runGenerator(invalidManifest, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /safe relative package path/);
    await assert.rejects(readdir(output), { code: "ENOENT" });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
