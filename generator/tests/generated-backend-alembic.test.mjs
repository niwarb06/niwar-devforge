import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repositoryRoot = dirname(generatorRoot);
const generatorPath = join(generatorRoot, "generate.mjs");
const manifestPath = join(generatorRoot, "manifests", "backend-auth-proof.json");

const canonicalFiles = [
  ["alembic.ini", "alembic.ini"],
  [join("migrations", "env.py"), join("migrations", "env.py")],
  [
    join("migrations", "script.py.mako"),
    join("migrations", "script.py.mako"),
  ],
];

test("backend blueprint emits canonical Alembic runner/config without executing migrations", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-backend-alembic-"));
  try {
    const output = join(root, "output");
    const run = spawnSync(
      process.execPath,
      [generatorPath, "--manifest", manifestPath, "--output", output],
      { encoding: "utf8" },
    );
    assert.equal(run.status, 0, run.stderr);

    for (const [generatedPath, canonicalPath] of canonicalFiles) {
      const generated = await readFile(join(output, generatedPath), "utf8");
      const canonical = await readFile(
        join(repositoryRoot, "packages", "backend-core", canonicalPath),
        "utf8",
      );
      assert.equal(
        generated,
        canonical,
        `${generatedPath} must match backend-core byte-for-byte`,
      );
    }

    const readme = await readFile(join(output, "README.md"), "utf8");
    assert.match(readme, /python -m alembic upgrade head/);
    assert.match(readme, /never executes migrations automatically/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
