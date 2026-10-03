import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const manifestNames = ["web-auth-proof.json", "flutter-auth-proof.json"];

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
  test(`${manifestName} emits the source-backed local Docker dev setup`, async () => {
    const root = await mkdtemp(join(tmpdir(), "devforge-generated-dev-"));
    try {
      const output = join(root, "output");
      const manifest = JSON.parse(
        await readFile(join(generatorRoot, "manifests", manifestName), "utf8"),
      );
      const run = runGenerator(manifestName, output);
      assert.equal(run.status, 0, run.stderr);

      const compose = await readFile(
        join(output, "infrastructure", "dev", "docker-compose.yml"),
        "utf8",
      );
      const envExample = await readFile(
        join(output, "infrastructure", "dev", ".env.example"),
        "utf8",
      );

      assert.ok(compose.startsWith(`name: ${manifest.product.slug}-dev\n`));
      assert.match(compose, /image: postgres:16-alpine/);
      assert.match(compose, /image: valkey\/valkey:7\.2\.14-alpine/);
      assert.match(
        compose,
        /POSTGRES_PASSWORD: \$\{POSTGRES_PASSWORD:\?Set POSTGRES_PASSWORD in infrastructure\/dev\/\.env\}/,
      );
      assert.match(compose, /pg_isready -U \$\$POSTGRES_USER -d \$\$POSTGRES_DB/);
      assert.match(compose, /test: \["CMD", "valkey-cli", "ping"\]/);
      assert.equal((compose.match(/^\s+image:/gm) ?? []).length, 2);
      assert.doesNotMatch(compose, /^\s+build:/m);
      assert.doesNotMatch(compose, /\bdeploy\b|\bstaging\b|\bproduction\b/i);

      assert.equal(
        envExample,
        "POSTGRES_DB=devforge\nPOSTGRES_USER=devforge\nPOSTGRES_PASSWORD=<set-a-local-dev-password>\n",
      );
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
}
