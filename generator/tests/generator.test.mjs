import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const proofManifestPath = join(generatorRoot, "manifests", "web-auth-proof.json");

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

test("same manifest produces byte-identical generated output", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-determinism-"));
  try {
    const first = join(root, "first");
    const second = join(root, "second");
    const firstRun = runGenerator(proofManifestPath, first);
    const secondRun = runGenerator(proofManifestPath, second);
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.deepEqual(await snapshot(first), await snapshot(second));

    const generation = JSON.parse(await readFile(join(first, ".devforge-generation.json"), "utf8"));
    assert.equal(generation.generator_version, "0.1.0");
    assert.equal(generation.blueprint, "web-next-auth");
    assert.equal("generated_at" in generation, false);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("invalid product slug fails before output is written", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-invalid-"));
  try {
    const manifest = JSON.parse(await readFile(proofManifestPath, "utf8"));
    manifest.product.slug = "../escape";
    const manifestPath = join(root, "manifest.json");
    const output = join(root, "output");
    await writeFile(manifestPath, JSON.stringify(manifest), "utf8");

    const run = runGenerator(manifestPath, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /product\.slug/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("non-empty output directory is never overwritten", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-overwrite-"));
  try {
    const output = join(root, "output");
    await mkdir(output);
    await writeFile(join(output, "keep.txt"), "keep\n", "utf8");

    const run = runGenerator(proofManifestPath, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /must not already contain files/);
    assert.equal(await readFile(join(output, "keep.txt"), "utf8"), "keep\n");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
