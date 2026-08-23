import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const standaloneManifest = join(generatorRoot, "manifests", "web-auth-standalone-proof.json");

function digest(content) {
  return createHash("sha256").update(content).digest("hex");
}

function run(bundle, output) {
  return spawnSync(
    process.execPath,
    [
      generatorPath,
      "--manifest",
      standaloneManifest,
      "--package-bundle",
      bundle,
      "--output",
      output,
    ],
    { encoding: "utf8" },
  );
}

async function makeWebBundle(root, { tamper = false, mismatch = false } = {}) {
  const npm = join(root, "npm");
  await mkdir(npm, { recursive: true });
  const bff = Buffer.from("bff-package-proof\n");
  const session = Buffer.from("session-package-proof\n");
  await writeFile(join(npm, "bff.tgz"), bff);
  await writeFile(join(npm, "session.tgz"), session);
  const descriptor = {
    schema_version: 1,
    modules: {
      "web-bff-core": {
        kind: "file",
        source: "npm/bff.tgz",
        destination: mismatch ? "vendor/wrong.tgz" : "vendor/web-bff-core-0.1.0.tgz",
        sha256: tamper ? "0".repeat(64) : digest(bff),
      },
      "web-session-core": {
        kind: "file",
        source: "npm/session.tgz",
        destination: "vendor/web-session-core-0.1.0.tgz",
        sha256: digest(session),
      },
    },
  };
  await writeFile(join(root, "bundle.json"), `${JSON.stringify(descriptor)}\n`, "utf8");
}

test("verified package bundle is copied inside generated product", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-bundle-ok-"));
  try {
    const bundle = join(root, "bundle");
    const output = join(root, "product");
    await makeWebBundle(bundle);
    const result = run(bundle, output);
    assert.equal(result.status, 0, result.stderr);
    assert.equal(await readFile(join(output, "vendor", "web-bff-core-0.1.0.tgz"), "utf8"), "bff-package-proof\n");
    const record = JSON.parse(await readFile(join(output, ".devforge-generation.json"), "utf8"));
    assert.equal(record.dependency_mode, "verified-vendored-bundle");
    assert.match(record.vendored_packages["web-bff-core"].sha256, /^[0-9a-f]{64}$/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("tampered bundle artifact fails SHA-256 verification", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-bundle-tamper-"));
  try {
    const bundle = join(root, "bundle");
    await makeWebBundle(bundle, { tamper: true });
    const result = run(bundle, join(root, "product"));
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /failed SHA-256 verification/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("bundle destination must exactly match generated dependency spec", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-bundle-destination-"));
  try {
    const bundle = join(root, "bundle");
    await makeWebBundle(bundle, { mismatch: true });
    const result = run(bundle, join(root, "product"));
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /destination does not match/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
