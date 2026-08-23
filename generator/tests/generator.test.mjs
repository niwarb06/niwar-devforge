import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const webProofManifestPath = join(generatorRoot, "manifests", "web-auth-proof.json");
const flutterProofManifestPath = join(generatorRoot, "manifests", "flutter-auth-proof.json");

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

async function assertDeterministic(manifestPath, expectedBlueprint) {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-determinism-"));
  try {
    const first = join(root, "first");
    const second = join(root, "second");
    const firstRun = runGenerator(manifestPath, first);
    const secondRun = runGenerator(manifestPath, second);
    assert.equal(firstRun.status, 0, firstRun.stderr);
    assert.equal(secondRun.status, 0, secondRun.stderr);
    assert.deepEqual(await snapshot(first), await snapshot(second));

    const generation = JSON.parse(await readFile(join(first, ".devforge-generation.json"), "utf8"));
    assert.equal(generation.generator_version, "0.3.0");
    assert.equal(generation.blueprint, expectedBlueprint);
    assert.equal("generated_at" in generation, false);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("web manifest produces byte-identical generated output", async () => {
  await assertDeterministic(webProofManifestPath, "web-next-auth");
});

test("Flutter manifest produces byte-identical generated output", async () => {
  await assertDeterministic(flutterProofManifestPath, "flutter-mobile-auth");
});

test("invalid product slug fails before output is written", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-invalid-"));
  try {
    const manifest = JSON.parse(await readFile(webProofManifestPath, "utf8"));
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

test("unsupported blueprint fails closed", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-blueprint-"));
  try {
    const manifest = JSON.parse(await readFile(webProofManifestPath, "utf8"));
    manifest.blueprint = "unknown-blueprint";
    const manifestPath = join(root, "manifest.json");
    const output = join(root, "output");
    await writeFile(manifestPath, JSON.stringify(manifest), "utf8");

    const run = runGenerator(manifestPath, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /blueprint must be one of/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("Flutter package path cannot be absolute or shell-like", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-generator-flutter-path-"));
  try {
    const manifest = JSON.parse(await readFile(flutterProofManifestPath, "utf8"));
    manifest.package_specs["flutter-auth-core"] = "/tmp/flutter-auth-core";
    const manifestPath = join(root, "manifest.json");
    const output = join(root, "output");
    await writeFile(manifestPath, JSON.stringify(manifest), "utf8");

    const run = runGenerator(manifestPath, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /safe relative package path/);
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

    const run = runGenerator(webProofManifestPath, output);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /must not already contain files/);
    assert.equal(await readFile(join(output, "keep.txt"), "utf8"), "keep\n");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
