import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, readdir, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const generatorPath = join(generatorRoot, "generate.mjs");
const standaloneManifest = join(generatorRoot, "manifests", "web-auth-standalone-proof.json");
const backendStandaloneManifest = join(
  generatorRoot,
  "manifests",
  "backend-auth-standalone-proof.json",
);

function digest(content) {
  return createHash("sha256").update(content).digest("hex");
}

async function digestDirectory(root) {
  const entries = (await readdir(root, { recursive: true, withFileTypes: true }))
    .filter((entry) => entry.isFile())
    .map((entry) => join(entry.parentPath, entry.name))
    .sort((left, right) => relative(root, left).localeCompare(relative(root, right)));
  const hash = createHash("sha256");
  for (const path of entries) {
    hash.update(relative(root, path).replaceAll("\\", "/"));
    hash.update("\0");
    hash.update(await readFile(path));
    hash.update("\0");
  }
  return hash.digest("hex");
}

function run(bundle, output, manifest = standaloneManifest) {
  return spawnSync(
    process.execPath,
    [
      generatorPath,
      "--manifest",
      manifest,
      "--package-bundle",
      bundle,
      "--output",
      output,
    ],
    { encoding: "utf8" },
  );
}

async function assertMissing(path) {
  await assert.rejects(stat(path), (error) => error?.code === "ENOENT");
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

async function makeBackendBundle(root) {
  const source = join(root, "packages", "niwar-devforge-backend-core-0.1.0");
  await mkdir(join(source, "src", "devforge_core"), { recursive: true });
  await writeFile(
    join(source, "pyproject.toml"),
    '[project]\nname = "niwar-devforge-backend-core"\nversion = "0.1.0"\n',
    "utf8",
  );
  await writeFile(
    join(source, "src", "devforge_core", "main.py"),
    "app = object()\n",
    "utf8",
  );
  const descriptor = {
    schema_version: 1,
    modules: {
      "backend-core": {
        kind: "directory",
        source: "packages/niwar-devforge-backend-core-0.1.0",
        destination: "vendor/niwar-devforge-backend-core-0.1.0",
        sha256: await digestDirectory(source),
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
    assert.equal(
      await readFile(join(output, "vendor", "web-bff-core-0.1.0.tgz"), "utf8"),
      "bff-package-proof\n",
    );
    const record = JSON.parse(
      await readFile(join(output, ".devforge-generation.json"), "utf8"),
    );
    assert.equal(record.dependency_mode, "verified-vendored-bundle");
    assert.match(
      record.vendored_packages["web-bff-core"].sha256,
      /^[0-9a-f]{64}$/,
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("verified backend directory bundle is copied inside generated product", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-backend-bundle-ok-"));
  try {
    const bundle = join(root, "bundle");
    const output = join(root, "product");
    await makeBackendBundle(bundle);
    const result = run(bundle, output, backendStandaloneManifest);
    assert.equal(result.status, 0, result.stderr);
    assert.match(
      await readFile(
        join(
          output,
          "vendor",
          "niwar-devforge-backend-core-0.1.0",
          "pyproject.toml",
        ),
        "utf8",
      ),
      /name = "niwar-devforge-backend-core"/,
    );
    assert.equal(
      await readFile(join(output, "requirements.txt"), "utf8"),
      "vendor/niwar-devforge-backend-core-0.1.0\n",
    );
    const record = JSON.parse(
      await readFile(join(output, ".devforge-generation.json"), "utf8"),
    );
    assert.equal(record.dependency_mode, "verified-vendored-bundle");
    assert.equal(
      record.vendored_packages["backend-core"].destination,
      "vendor/niwar-devforge-backend-core-0.1.0",
    );
    assert.match(record.vendored_packages["backend-core"].sha256, /^[0-9a-f]{64}$/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("tampered bundle artifact fails before output is written", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-bundle-tamper-"));
  try {
    const bundle = join(root, "bundle");
    const output = join(root, "product");
    await makeWebBundle(bundle, { tamper: true });
    const result = run(bundle, output);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /failed SHA-256 verification/);
    await assertMissing(output);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("bundle destination mismatch fails before output is written", async () => {
  const root = await mkdtemp(join(tmpdir(), "devforge-bundle-destination-"));
  try {
    const bundle = join(root, "bundle");
    const output = join(root, "product");
    await makeWebBundle(bundle, { mismatch: true });
    const result = run(bundle, output);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /destination does not match/);
    await assertMissing(output);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
