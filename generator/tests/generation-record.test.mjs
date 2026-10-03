import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const validatorPath = join(generatorRoot, "validate-generation-record.mjs");
const webManifestPath = join(generatorRoot, "manifests", "web-auth-proof.json");
const flutterManifestPath = join(generatorRoot, "manifests", "flutter-auth-proof.json");

function runGenerator(manifest, output) {
  return spawnSync(process.execPath, [generatorPath, "--manifest", manifest, "--output", output], {
    encoding: "utf8",
  });
}

function runValidator(record) {
  return spawnSync(process.execPath, [validatorPath, record], { encoding: "utf8" });
}

async function generateRecord(root, manifestPath, name) {
  const output = join(root, name);
  const generated = runGenerator(manifestPath, output);
  assert.equal(generated.status, 0, generated.stderr);
  return join(output, ".devforge-generation.json");
}

test("generated Web and Flutter documentation manifests validate", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generation-record-valid-"));
  try {
    for (const [manifest, name] of [
      [webManifestPath, "web"],
      [flutterManifestPath, "flutter"],
    ]) {
      const record = await generateRecord(root, manifest, name);
      const validated = runValidator(record);
      assert.equal(validated.status, 0, validated.stderr);
      assert.match(validated.stdout, /generation record valid/);
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("selected product pack documentation is checked against its committed contract", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generation-record-pack-"));
  try {
    const manifest = JSON.parse(await readFile(webManifestPath, "utf8"));
    manifest.pack = "business";
    const manifestPath = join(root, "manifest.json");
    await writeFile(manifestPath, JSON.stringify(manifest), "utf8");
    const record = await generateRecord(root, manifestPath, "output");

    const validated = runValidator(record);
    assert.equal(validated.status, 0, validated.stderr);

    const value = JSON.parse(await readFile(record, "utf8"));
    value.pack.capabilities = [...value.pack.capabilities].reverse();
    const invalid = join(root, "invalid-pack.json");
    await writeFile(invalid, JSON.stringify(value), "utf8");
    const rejected = runValidator(invalid);
    assert.notEqual(rejected.status, 0);
    assert.match(rejected.stderr, /pack\.capabilities/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("unknown documentation-manifest keys fail closed", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generation-record-unknown-"));
  try {
    const recordPath = await generateRecord(root, webManifestPath, "output");
    const record = JSON.parse(await readFile(recordPath, "utf8"));
    record.generated_at = "2026-10-04T00:00:00Z";
    const invalid = join(root, "invalid.json");
    await writeFile(invalid, JSON.stringify(record), "utf8");

    const rejected = runValidator(invalid);
    assert.notEqual(rejected.status, 0);
    assert.match(rejected.stderr, /unsupported key/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("vendored documentation requires complete safe dependency provenance", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generation-record-vendored-"));
  try {
    const recordPath = await generateRecord(root, webManifestPath, "output");
    const record = JSON.parse(await readFile(recordPath, "utf8"));
    record.dependency_mode = "verified-vendored-bundle";
    record.package_specs = {
      "web-bff-core": "file:vendor/web-bff-core.tgz",
      "web-session-core": "file:vendor/web-session-core.tgz",
    };
    record.vendored_packages = {
      "web-bff-core": {
        destination: "vendor/web-bff-core.tgz",
        sha256: "a".repeat(64),
      },
      "web-session-core": {
        destination: "vendor/web-session-core.tgz",
        sha256: "b".repeat(64),
      },
    };
    const valid = join(root, "vendored-valid.json");
    await writeFile(valid, JSON.stringify(record), "utf8");
    assert.equal(runValidator(valid).status, 0);

    record.vendored_packages["web-bff-core"].destination = "vendor/../escape.tgz";
    const invalid = join(root, "vendored-invalid.json");
    await writeFile(invalid, JSON.stringify(record), "utf8");
    const rejected = runValidator(invalid);
    assert.notEqual(rejected.status, 0);
    assert.match(rejected.stderr, /safe vendor/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
