import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");

const manifests = Object.freeze({
  web: join(generatorRoot, "manifests", "web-auth-proof.json"),
  mobile: join(generatorRoot, "manifests", "flutter-auth-proof.json"),
  admin: join(generatorRoot, "manifests", "admin-auth-proof.json"),
  backend: join(generatorRoot, "manifests", "backend-auth-proof.json"),
});

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

async function assertGeneratedFile(root, path) {
  const content = await readFile(join(root, path), "utf8");
  assert.ok(content.length > 0, path + " must not be empty");
  return content;
}

test("Phase 5 roadmap baseline is evidenced by deterministic generated products", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-phase5-acceptance-"));
  try {
    const webWithPack = JSON.parse(await readFile(manifests.web, "utf8"));
    webWithPack.pack = "business";
    const webWithPackPath = join(root, "web-with-pack.json");
    await writeFile(webWithPackPath, JSON.stringify(webWithPack), "utf8");

    const cases = [
      {
        name: "web",
        manifest: webWithPackPath,
        expectedBlueprint: "web-next-auth",
        testSkeleton: "test/scaffold.test.mjs",
        rootEnvironmentExample: true,
      },
      {
        name: "mobile",
        manifest: manifests.mobile,
        expectedBlueprint: "flutter-mobile-auth",
        testSkeleton: "test/auth_screen_test.dart",
        rootEnvironmentExample: false,
      },
      {
        name: "admin",
        manifest: manifests.admin,
        expectedBlueprint: "web-next-auth",
        testSkeleton: "test/scaffold.test.mjs",
        rootEnvironmentExample: true,
      },
      {
        name: "backend",
        manifest: manifests.backend,
        expectedBlueprint: "backend-fastapi-auth",
        testSkeleton: "tests/test_scaffold.py",
        rootEnvironmentExample: true,
      },
    ];

    for (const item of cases) {
      const first = join(root, item.name + "-first");
      const second = join(root, item.name + "-second");
      const firstRun = runGenerator(item.manifest, first);
      const secondRun = runGenerator(item.manifest, second);

      assert.equal(
        firstRun.status,
        0,
        item.name + " first generation failed: " + firstRun.stderr,
      );
      assert.equal(
        secondRun.status,
        0,
        item.name + " second generation failed: " + secondRun.stderr,
      );
      assert.deepEqual(
        await snapshot(first),
        await snapshot(second),
        item.name + " output must be byte-identical",
      );

      const manifest = JSON.parse(await readFile(item.manifest, "utf8"));
      const record = JSON.parse(
        await assertGeneratedFile(first, ".devforge-generation.json"),
      );
      assert.equal(record.blueprint, item.expectedBlueprint);
      assert.deepEqual(record.product, manifest.product);
      assert.deepEqual(record.modules, manifest.modules);

      if (item.name === "web") {
        assert.deepEqual(record.pack, {
          name: "business",
          schema_version: 1,
          capabilities: ["crud", "dashboards", "reports", "roles", "export_import"],
        });
      }

      await assertGeneratedFile(first, ".github/workflows/ci.yml");
      await assertGeneratedFile(first, "infrastructure/dev/docker-compose.yml");
      await assertGeneratedFile(first, "infrastructure/dev/.env.example");
      await assertGeneratedFile(first, "migrations/versions/0001_backend_core_baseline.py");
      await assertGeneratedFile(first, "migrations/versions/0002_identity_sessions.py");
      await assertGeneratedFile(first, "migrations/versions/0003_roles_tenants.py");
      await assertGeneratedFile(first, item.testSkeleton);

      if (item.rootEnvironmentExample) {
        await assertGeneratedFile(first, ".env.example");
      } else {
        const readme = await assertGeneratedFile(first, "README.md");
        assert.match(readme, /DEVFORGE_BACKEND_API_BASE_URL/);
        assert.match(readme, /--dart-define=/);
      }
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
