#!/usr/bin/env node

import { createHash } from "node:crypto";
import { cp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { basename, dirname, join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(process.cwd(), process.argv[2] ?? ".devforge-package-bundle");

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

async function npmEntry(bundleRoot, packageDir, destinationName) {
  const npmDir = join(bundleRoot, "npm");
  await mkdir(npmDir, { recursive: true });
  const stdout = run("npm", ["pack", "--pack-destination", npmDir], packageDir);
  const packedName = basename(stdout.split(/\r?\n/).at(-1));
  const source = `npm/${packedName}`;
  return {
    kind: "file",
    source,
    destination: `vendor/${destinationName}`,
    sha256: await shaFile(join(bundleRoot, source)),
  };
}

await rm(output, { recursive: true, force: true });
const webRoot = join(output, "web");
const flutterRoot = join(output, "flutter");
await mkdir(webRoot, { recursive: true });
await mkdir(flutterRoot, { recursive: true });

const bff = await npmEntry(
  webRoot,
  join(root, "packages/web-bff-core"),
  "web-bff-core-0.1.0.tgz",
);
const session = await npmEntry(
  webRoot,
  join(root, "packages/web-session-core"),
  "web-session-core-0.1.0.tgz",
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
const flutterSourceRelative = "packages/niwar_devforge_flutter_auth-0.1.0";
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
        destination: "vendor/niwar_devforge_flutter_auth-0.1.0",
        sha256: await shaDir(flutterOut),
      },
    },
  }, null, 2)}\n`,
  "utf8",
);

console.log(`Built Web package bundle at ${webRoot}`);
console.log(`Built Flutter package bundle at ${flutterRoot}`);
