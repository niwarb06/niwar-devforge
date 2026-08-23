#!/usr/bin/env node

import { createHash } from "node:crypto";
import { cp, copyFile, mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const GENERATOR_VERSION = "0.3.0";
const TOKEN_PATTERN = /\{\{([A-Z0-9_]+)\}\}/g;
const SLUG_PATTERN = /^[a-z][a-z0-9-]{1,47}[a-z0-9]$/;
const NPM_PACKAGE_PATTERN = /^@[a-z0-9][a-z0-9._-]*\/[a-z0-9][a-z0-9._-]*$/;
const DART_PACKAGE_PATTERN = /^[a-z][a-z0-9_]{1,62}[a-z0-9]$/;
const SAFE_NPM_SPEC_PATTERN = /^(?:file:\.{1,2}\/|[~^]?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\S*$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

const generatorRoot = dirname(fileURLToPath(import.meta.url));

function fail(message) {
  throw new Error(`DevForge generator: ${message}`);
}

function validateFlutterPackagePath(spec) {
  if (
    typeof spec !== "string" ||
    spec.length < 4 ||
    spec.length > 240 ||
    isAbsolute(spec) ||
    spec.includes("\\") ||
    /[\r\n\0]/.test(spec)
  ) return false;

  const parts = spec.split("/");
  if (parts.some((part) => !part || part === "." || !/^[A-Za-z0-9._-]+$/.test(part))) return false;
  if (parts[0] === "vendor") return parts.length >= 2;

  let parentSegments = 0;
  while (parts[parentSegments] === "..") parentSegments += 1;
  if (parentSegments === 0 || parentSegments === parts.length) return false;
  return parts.slice(parentSegments).every((part) => part !== ".." && /^[A-Za-z0-9._-]+$/.test(part));
}

const BLUEPRINTS = Object.freeze({
  "web-next-auth": Object.freeze({
    modules: Object.freeze(["web-bff-core", "web-session-core"]),
    packageNamePattern: NPM_PACKAGE_PATTERN,
    packageNameError: "product.package_name must be a lowercase scoped npm package name",
    validatePackageSpec: (spec) =>
      typeof spec === "string" && SAFE_NPM_SPEC_PATTERN.test(spec) && !/[\r\n\0]/.test(spec),
    packageSpecError: (moduleName) => `package_specs.${moduleName} is not an allowed npm package spec`,
    tokens: (manifest) => ({
      WEB_BFF_SPEC: manifest.package_specs["web-bff-core"],
      WEB_SESSION_SPEC: manifest.package_specs["web-session-core"],
    }),
  }),
  "flutter-mobile-auth": Object.freeze({
    modules: Object.freeze(["flutter-auth-core"]),
    packageNamePattern: DART_PACKAGE_PATTERN,
    packageNameError: "product.package_name must be a lowercase Dart package name",
    validatePackageSpec: validateFlutterPackagePath,
    packageSpecError: (moduleName) => `package_specs.${moduleName} must be a safe relative package path`,
    tokens: (manifest) => ({ FLUTTER_AUTH_PATH: manifest.package_specs["flutter-auth-core"] }),
  }),
});

function parseArgs(argv) {
  const args = { manifest: null, output: null, packageBundle: null };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--manifest" || flag === "--output" || flag === "--package-bundle") {
      if (!value || value.startsWith("--")) fail(`${flag} requires a value`);
      const key = flag === "--package-bundle" ? "packageBundle" : flag.slice(2);
      args[key] = value;
      index += 1;
      continue;
    }
    fail(`unknown argument ${flag}`);
  }
  if (!args.manifest) fail("--manifest is required");
  if (!args.output) fail("--output is required");
  return args;
}

function assertPlainObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} must be an object`);
}

function assertExactKeys(value, allowed, label) {
  const extras = Object.keys(value).filter((key) => !allowed.has(key));
  if (extras.length > 0) fail(`${label} contains unsupported keys: ${extras.join(", ")}`);
}

function validateManifest(value) {
  assertPlainObject(value, "manifest");
  assertExactKeys(value, new Set(["schema_version", "blueprint", "product", "modules", "package_specs"]), "manifest");
  if (value.schema_version !== 1) fail("schema_version must equal 1");
  if (typeof value.blueprint !== "string" || !(value.blueprint in BLUEPRINTS)) {
    fail(`blueprint must be one of ${JSON.stringify(Object.keys(BLUEPRINTS))}`);
  }
  const blueprint = BLUEPRINTS[value.blueprint];
  assertPlainObject(value.product, "product");
  assertExactKeys(value.product, new Set(["slug", "display_name", "package_name"]), "product");
  if (typeof value.product.slug !== "string" || !SLUG_PATTERN.test(value.product.slug)) fail("product.slug must be a lowercase 3-49 character safe slug");
  if (typeof value.product.display_name !== "string" || value.product.display_name.trim() !== value.product.display_name || value.product.display_name.length < 2 || value.product.display_name.length > 80 || /[\r\n\0]/.test(value.product.display_name)) {
    fail("product.display_name must be a trimmed 2-80 character single-line value");
  }
  if (typeof value.product.package_name !== "string" || !blueprint.packageNamePattern.test(value.product.package_name)) fail(blueprint.packageNameError);
  if (!Array.isArray(value.modules) || value.modules.length !== blueprint.modules.length || !blueprint.modules.every((moduleName, index) => value.modules[index] === moduleName)) {
    fail(`modules must equal ${JSON.stringify(blueprint.modules)}`);
  }
  assertPlainObject(value.package_specs, "package_specs");
  assertExactKeys(value.package_specs, new Set(blueprint.modules), "package_specs");
  for (const moduleName of blueprint.modules) {
    if (!blueprint.validatePackageSpec(value.package_specs[moduleName])) fail(blueprint.packageSpecError(moduleName));
  }
  return { manifest: value, blueprint };
}

function validateTemplateFiles(value) {
  assertPlainObject(value, "template");
  const files = Object.entries(value);
  if (files.length === 0) fail("template must contain files");
  for (const [path, content] of files) {
    if (!path || isAbsolute(path) || path.includes("\\") || path.split("/").some((part) => part === ".." || part === "." || part === "")) fail(`unsafe template path ${JSON.stringify(path)}`);
    if (typeof content !== "string") fail(`template content for ${path} must be a string`);
  }
  return files.sort(([left], [right]) => left.localeCompare(right));
}

function render(content, tokens, path) {
  const rendered = content.replace(TOKEN_PATTERN, (_, token) => {
    if (!(token in tokens)) fail(`unknown template token ${token} in ${path}`);
    return tokens[token];
  });
  TOKEN_PATTERN.lastIndex = 0;
  if (TOKEN_PATTERN.test(rendered)) fail(`unresolved template token in ${path}`);
  TOKEN_PATTERN.lastIndex = 0;
  return rendered.endsWith("\n") ? rendered : `${rendered}\n`;
}

async function ensureEmptyOutput(outputRoot) {
  try {
    const info = await stat(outputRoot);
    if (!info.isDirectory()) fail("output exists and is not a directory");
    const entries = await readdir(outputRoot);
    if (entries.length > 0) fail("output directory must not already contain files");
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") return;
    throw error;
  }
}

function safeDestination(root, path, label = "path") {
  const destination = resolve(root, path);
  const rel = relative(root, destination);
  if (!rel || rel.startsWith(`..${sep}`) || rel === ".." || isAbsolute(rel)) fail(`${label} escapes root: ${path}`);
  return destination;
}

function bundleDestinationForSpec(spec) {
  return spec.startsWith("file:./") ? spec.slice("file:./".length) : spec;
}

async function hashFile(path) {
  const hash = createHash("sha256");
  hash.update(await readFile(path));
  return hash.digest("hex");
}

async function hashDirectory(root) {
  const files = [];
  async function walk(dir) {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) await walk(path);
      else if (entry.isFile()) files.push(path);
      else fail("package bundle directories may contain only regular files/directories");
    }
  }
  await walk(root);
  files.sort((a, b) => relative(root, a).localeCompare(relative(root, b)));
  const hash = createHash("sha256");
  for (const path of files) {
    hash.update(relative(root, path).replaceAll(sep, "/"));
    hash.update("\0");
    hash.update(await readFile(path));
    hash.update("\0");
  }
  return hash.digest("hex");
}

async function vendorPackageBundle(bundleRoot, outputRoot, manifest, blueprint) {
  const descriptorPath = join(bundleRoot, "bundle.json");
  const descriptor = JSON.parse(await readFile(descriptorPath, "utf8"));
  assertPlainObject(descriptor, "package bundle");
  assertExactKeys(descriptor, new Set(["schema_version", "modules"]), "package bundle");
  if (descriptor.schema_version !== 1) fail("package bundle schema_version must equal 1");
  assertPlainObject(descriptor.modules, "package bundle modules");
  assertExactKeys(descriptor.modules, new Set(blueprint.modules), "package bundle modules");

  const vendored = {};
  for (const moduleName of blueprint.modules) {
    const entry = descriptor.modules[moduleName];
    assertPlainObject(entry, `package bundle modules.${moduleName}`);
    assertExactKeys(entry, new Set(["kind", "source", "destination", "sha256"]), `package bundle modules.${moduleName}`);
    if (!new Set(["file", "directory"]).has(entry.kind)) fail(`package bundle modules.${moduleName}.kind is invalid`);
    for (const key of ["source", "destination"]) {
      if (typeof entry[key] !== "string" || !entry[key] || isAbsolute(entry[key]) || entry[key].includes("\\") || entry[key].split("/").some((part) => !part || part === "." || part === "..")) fail(`package bundle modules.${moduleName}.${key} is unsafe`);
    }
    if (typeof entry.sha256 !== "string" || !SHA256_PATTERN.test(entry.sha256)) fail(`package bundle modules.${moduleName}.sha256 is invalid`);
    const expectedDestination = bundleDestinationForSpec(manifest.package_specs[moduleName]);
    if (entry.destination !== expectedDestination || !entry.destination.startsWith("vendor/")) fail(`package bundle destination does not match package_specs.${moduleName}`);

    const source = safeDestination(bundleRoot, entry.source, "package bundle source");
    const sourceInfo = await stat(source);
    if ((entry.kind === "file") !== sourceInfo.isFile() || (entry.kind === "directory") !== sourceInfo.isDirectory()) fail(`package bundle modules.${moduleName} kind does not match source`);
    const actualHash = entry.kind === "file" ? await hashFile(source) : await hashDirectory(source);
    if (actualHash !== entry.sha256) fail(`package bundle modules.${moduleName} failed SHA-256 verification`);

    const destination = safeDestination(outputRoot, entry.destination, "package bundle destination");
    await mkdir(dirname(destination), { recursive: true });
    if (entry.kind === "file") await copyFile(source, destination);
    else await cp(source, destination, { recursive: true, errorOnExist: true, force: false });
    vendored[moduleName] = { destination: entry.destination, sha256: entry.sha256 };
  }
  return vendored;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifestPath = resolve(process.cwd(), args.manifest);
  const outputRoot = resolve(process.cwd(), args.output);
  const { manifest, blueprint } = validateManifest(JSON.parse(await readFile(manifestPath, "utf8")));
  const templatePath = join(generatorRoot, "templates", manifest.blueprint, "files.json");
  const templateFiles = validateTemplateFiles(JSON.parse(await readFile(templatePath, "utf8")));

  await ensureEmptyOutput(outputRoot);
  await mkdir(outputRoot, { recursive: true });

  const tokens = { PRODUCT_NAME: manifest.product.display_name, PRODUCT_SLUG: manifest.product.slug, PACKAGE_NAME: manifest.product.package_name, ...blueprint.tokens(manifest) };
  for (const [templateFile, templateContent] of templateFiles) {
    const destination = safeDestination(outputRoot, templateFile, "template path");
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, render(templateContent, tokens, templateFile), { encoding: "utf8", flag: "wx" });
  }

  const vendored_packages = args.packageBundle
    ? await vendorPackageBundle(resolve(process.cwd(), args.packageBundle), outputRoot, manifest, blueprint)
    : null;

  const generationRecord = {
    schema_version: 1,
    generator: "niwar-devforge",
    generator_version: GENERATOR_VERSION,
    blueprint: manifest.blueprint,
    product: manifest.product,
    modules: manifest.modules,
    package_specs: manifest.package_specs,
    dependency_mode: vendored_packages ? "verified-vendored-bundle" : "manifest-specs",
    ...(vendored_packages ? { vendored_packages } : {}),
  };
  await writeFile(join(outputRoot, ".devforge-generation.json"), `${JSON.stringify(generationRecord, null, 2)}\n`, { encoding: "utf8", flag: "wx" });

  console.log(`Generated ${manifest.product.slug} with ${templateFiles.length} template files using ${manifest.blueprint}.`);
}

await main();
