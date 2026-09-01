#!/usr/bin/env node

import { createHash } from "node:crypto";
import { cp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { basename, dirname, join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(process.cwd(), process.argv[2] ?? ".devforge-package-bundle");
const VERSION_PATTERN = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;

function fail(message) {
  throw new Error(`DevForge package bundle: ${message}`);
}

function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, encoding: "utf8" });
  if (result.status !== 0) fail(`${command} failed: ${result.stderr || result.stdout}`);
  return result.stdout.trim();
}

async function shaFile(path) {
  const hash = createHash("sha256");
  hash.update(await readFile(path));
  return hash.digest("hex");
}

async function shaDir(dir) {
  const files = [];
  async function walk(current) {
    for (const entry of await readdir(current, { withFileTypes: true })) {
      const path = join(current, entry.name);
      if (entry.isDirectory()) await walk(path);
      else if (entry.isFile()) files.push(path);
      else fail("package source contains an unsupported filesystem entry");
    }
  }
  await walk(dir);
  files.sort((left, right) => relative(dir, left).localeCompare(relative(dir, right)));
  const hash = createHash("sha256");
  for (const path of files) {
    hash.update(relative(dir, path).replaceAll(sep, "/"));
    hash.update("\0");
    hash.update(await readFile(path));
    hash.update("\0");
  }
  return hash.digest("hex");
}

async function npmMetadata(packageDir, expectedName) {
  const metadata = JSON.parse(await readFile(join(packageDir, "package.json"), "utf8"));
  if (metadata.name !== expectedName) fail(`${packageDir} package name is unexpected`);
  if (typeof metadata.version !== "string" || !VERSION_PATTERN.test(metadata.version)) {
    fail(`${packageDir} version must be a simple semantic version`);
  }
  return metadata;
}

async function npmEntry(bundleRoot, packageDir, moduleName, expectedName) {
  const metadata = await npmMetadata(packageDir, expectedName);
  const npmDir = join(bundleRoot, "npm");
  await mkdir(npmDir, { recursive: true });
  const stdout = run("npm", ["pack", "--pack-destination", npmDir], packageDir);
  const packedName = basename(stdout.split(/\r?\n/).at(-1));
  const source = `npm/${packedName}`;
  return {
    kind: "file",
    source,
    destination: `vendor/${moduleName}-${metadata.version}.tgz`,
    sha256: await shaFile(join(bundleRoot, source)),
  };
}

async function flutterMetadata(packageDir) {
  const pubspec = await readFile(join(packageDir, "pubspec.yaml"), "utf8");
  const name = pubspec.match(/^name:\s*([A-Za-z0-9_]+)\s*$/m)?.[1];
  const version = pubspec.match(/^version:\s*([^\s]+)\s*$/m)?.[1];
  if (name !== "niwar_devforge_flutter_auth") fail("Flutter auth package name is unexpected");
  if (!version || !VERSION_PATTERN.test(version)) {
    fail("Flutter auth package version must be a simple semantic version");
  }
  return { name, version };
}

await rm(output, { recursive: true, force: true });
const webRoot = join(output, "web");
const flutterRoot = join(output, "flutter");
await mkdir(webRoot, { recursive: true });
await mkdir(flutterRoot, { recursive: true });

const bff = await npmEntry(
  webRoot,
  join(root, "packages/web-bff-core"),
  "web-bff-core",
  "@niwar-devforge/web-bff-core",
);
const session = await npmEntry(
  webRoot,
  join(root, "packages/web-session-core"),
  "web-session-core",
  "@niwar-devforge/web-session-core",
);
await writeFile(
  join(webRoot, "bundle.json"),
  `${JSON.stringify({
    schema_version: 1,
    modules: {
      "web-bff-core": bff,
      "web-session-core": session,
    },
  }, null, 2)}\n`,
  "utf8",
);

const flutterSource = join(root, "packages/flutter-auth-core");
const flutter = await flutterMetadata(flutterSource);
const flutterSourceRelative = `packages/${flutter.name}-${flutter.version}`;
const flutterDestination = `vendor/${flutter.name}-${flutter.version}`;
const flutterOut = join(flutterRoot, flutterSourceRelative);
await cp(flutterSource, flutterOut, {
  recursive: true,
  filter: (source) =>
    !source
      .split(/[\\/]/)
      .some((part) => part === ".dart_tool" || part === "build" || part === ".git"),
});
await writeFile(
  join(flutterRoot, "bundle.json"),
  `${JSON.stringify({
    schema_version: 1,
    modules: {
      "flutter-auth-core": {
        kind: "directory",
        source: flutterSourceRelative,
        destination: flutterDestination,
        sha256: await shaDir(flutterOut),
      },
    },
  }, null, 2)}\n`,
  "utf8",
);

console.log(`Built Web package bundle at ${webRoot}`);
console.log(`Built Flutter package bundle at ${flutterRoot}`);
