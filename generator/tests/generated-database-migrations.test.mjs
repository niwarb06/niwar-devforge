import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const repositoryRoot = dirname(generatorRoot);
const generatorPath = join(generatorRoot, "generate.mjs");
const manifestNames = ["web-auth-proof.json", "flutter-auth-proof.json"];
const migrationNames = [
  "0001_backend_core_baseline.py",
  "0002_identity_sessions.py",
  "0003_roles_tenants.py",
];

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

for (const manifestName of manifestNames) {
  test(`${manifestName} emits the canonical backend migration history`, async () => {
    const root = await mkdtemp(join(tmpdir(), "devforge-generated-migrations-"));
    try {
      const output = join(root, "output");
      const run = runGenerator(manifestName, output);
      assert.equal(run.status, 0, run.stderr);

      const generatedNames = await readdir(join(output, "migrations", "versions"));
      assert.deepEqual(generatedNames.sort(), migrationNames);

      for (const name of migrationNames) {
        const generated = await readFile(
          join(output, "migrations", "versions", name),
          "utf8",
        );
        const canonical = await readFile(
          join(
            repositoryRoot,
            "packages",
            "backend-core",
            "migrations",
            "versions",
            name,
          ),
          "utf8",
        );
        assert.equal(generated, canonical, `${name} must be copied byte-for-byte`);
      }

      const baseline = await readFile(
        join(output, "migrations", "versions", migrationNames[0]),
        "utf8",
      );
      const identity = await readFile(
        join(output, "migrations", "versions", migrationNames[1]),
        "utf8",
      );
      const roles = await readFile(
        join(output, "migrations", "versions", migrationNames[2]),
        "utf8",
      );
      assert.match(baseline, /revision: str = "0001_backend_core_baseline"/);
      assert.match(baseline, /down_revision: str \| None = None/);
      assert.match(identity, /revision: str = "0002_identity_sessions"/);
      assert.match(
        identity,
        /down_revision: str \| None = "0001_backend_core_baseline"/,
      );
      assert.match(roles, /revision: str = "0003_roles_tenants"/);
      assert.match(
        roles,
        /down_revision: str \| None = "0002_identity_sessions"/,
      );

      await assert.rejects(readFile(join(output, "alembic.ini"), "utf8"), {
        code: "ENOENT",
      });
      await assert.rejects(
        readFile(join(output, "migrations", "env.py"), "utf8"),
        { code: "ENOENT" },
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
}
