#!/usr/bin/env node

import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const GENERATOR_VERSION = "0.2.0";
const TOKEN_PATTERN = /\{\{([A-Z0-9_]+)\}\}/g;
const SLUG_PATTERN = /^[a-z][a-z0-9-]{1,47}[a-z0-9]$/;
const NPM_PACKAGE_PATTERN = /^@[a-z0-9][a-z0-9._-]*\/[a-z0-9][a-z0-9._-]*$/;
const DART_PACKAGE_PATTERN = /^[a-z][a-z0-9_]{1,62}[a-z0-9]$/;
const SAFE_NPM_SPEC_PATTERN = /^(?:file:\.{1,2}\/|[~^]?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\S*$/;

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
  ) {
    return false;
  }

  const parts = spec.split("/");
  let parentSegments = 0;
  while (parts[parentSegments] === "..") parentSegments += 1;
  if (parentSegments === 0 || parentSegments === parts.length) return false;

  return parts.slice(parentSegments).every(
    (part) =>
      part.length > 0 &&
      part !== "." &&
      part !== ".." &&
      /^[A-Za-z0-9._-]+$/.test(part),
  );
}

const BLUEPRINTS = Object.freeze({
  "web-next-auth": Object.freeze({
    modules: Object.freeze(["web-bff-core", "web-session-core"]),
    packageNamePattern: NPM_PACKAGE_PATTERN,
    packageNameError: "product.package_name must be a lowercase scoped npm package name",
    validatePackageSpec: (spec) =>
      typeof spec === "string" &&
      SAFE_NPM_SPEC_PATTERN.test(spec) &&
      !/[\r\n\0]/.test(spec),
    packageSpecError: (moduleName) =>
      `package_specs.${moduleName} is not an allowed npm package spec`,
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
    packageSpecError: (moduleName) =>
      `package_specs.${moduleName} must be a safe relative package path`,
    tokens: (manifest) => ({
      FLUTTER_AUTH_PATH: manifest.package_specs["flutter-auth-core"],
    }),
  }),
});

function parseArgs(argv) {
  const args = { manifest: null, output: null };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--manifest" || flag === "--output") {
      if (!value || value.startsWith("--")) fail(`${flag} requires a value`);
      args[flag.slice(2)] = value;
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
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    fail(`${label} must be an object`);
  }
}

function assertExactKeys(value, allowed, label) {
  const extras = Object.keys(value).filter((key) => !allowed.has(key));
  if (extras.length > 0) fail(`${label} contains unsupported keys: ${extras.join(", ")}`);
}

function validateManifest(value) {
  assertPlainObject(value, "manifest");
  assertExactKeys(
    value,
    new Set(["schema_version", "blueprint", "product", "modules", "package_specs"]),
    "manifest",
  );

  if (value.schema_version !== 1) fail("schema_version must equal 1");
  if (typeof value.blueprint !== "string" || !(value.blueprint in BLUEPRINTS)) {
    fail(`blueprint must be one of ${JSON.stringify(Object.keys(BLUEPRINTS))}`);
  }
  const blueprint = BLUEPRINTS[value.blueprint];

  assertPlainObject(value.product, "product");
  assertExactKeys(value.product, new Set(["slug", "display_name", "package_name"]), "product");
  if (typeof value.product.slug !== "string" || !SLUG_PATTERN.test(value.product.slug)) {
    fail("product.slug must be a lowercase 3-49 character safe slug");
  }
  if (
    typeof value.product.display_name !== "string" ||
    value.product.display_name.trim() !== value.product.display_name ||
    value.product.display_name.length < 2 ||
    value.product.display_name.length > 80 ||
    /[\r\n\0]/.test(value.product.display_name)
  ) {
    fail("product.display_name must be a trimmed 2-80 character single-line value");
  }
  if (
    typeof value.product.package_name !== "string" ||
    !blueprint.packageNamePattern.test(value.product.package_name)
  ) {
    fail(blueprint.packageNameError);
  }

  if (
    !Array.isArray(value.modules) ||
    value.modules.length !== blueprint.modules.length ||
    !blueprint.modules.every((moduleName, index) => value.modules[index] === moduleName)
  ) {
    fail(`modules must equal ${JSON.stringify(blueprint.modules)}`);
  }

  assertPlainObject(value.package_specs, "package_specs");
  assertExactKeys(value.package_specs, new Set(blueprint.modules), "package_specs");
  for (const moduleName of blueprint.modules) {
    const spec = value.package_specs[moduleName];
    if (!blueprint.validatePackageSpec(spec)) {
      fail(blueprint.packageSpecError(moduleName));
    }
  }

  return { manifest: value, blueprint };
}

function validateTemplateFiles(value) {
  assertPlainObject(value, "template");
  const files = Object.entries(value);
  if (files.length === 0) fail("template must contain files");
  for (const [path, content] of files) {
    if (
      !path ||
      isAbsolute(path) ||
      path.includes("\\") ||
      path.split("/").some((part) => part === ".." || part === "." || part === "")
    ) {
      fail(`unsafe template path ${JSON.stringify(path)}`);
    }
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

function safeDestination(outputRoot, templateFile) {
  const destination = resolve(outputRoot, templateFile);
  const rel = relative(outputRoot, destination);
  if (!rel || rel.startsWith(`..${sep}`) || rel === ".." || isAbsolute(rel)) {
    fail(`template path escapes output root: ${templateFile}`);
  }
  return destination;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifestPath = resolve(process.cwd(), args.manifest);
  const outputRoot = resolve(process.cwd(), args.output);
  const validated = validateManifest(JSON.parse(await readFile(manifestPath, "utf8")));
  const { manifest, blueprint } = validated;
  const templatePath = join(generatorRoot, "templates", manifest.blueprint, "files.json");
  const templateFiles = validateTemplateFiles(JSON.parse(await readFile(templatePath, "utf8")));

  await ensureEmptyOutput(outputRoot);
  await mkdir(outputRoot, { recursive: true });

  const tokens = {
    PRODUCT_NAME: manifest.product.display_name,
    PRODUCT_SLUG: manifest.product.slug,
    PACKAGE_NAME: manifest.product.package_name,
    ...blueprint.tokens(manifest),
  };

  for (const [templateFile, templateContent] of templateFiles) {
    const destination = safeDestination(outputRoot, templateFile);
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, render(templateContent, tokens, templateFile), {
      encoding: "utf8",
      flag: "wx",
    });
  }

  const generationRecord = {
    schema_version: 1,
    generator: "niwar-devforge",
    generator_version: GENERATOR_VERSION,
    blueprint: manifest.blueprint,
    product: manifest.product,
    modules: manifest.modules,
    package_specs: manifest.package_specs,
  };
  await writeFile(
    join(outputRoot, ".devforge-generation.json"),
    `${JSON.stringify(generationRecord, null, 2)}\n`,
    { encoding: "utf8", flag: "wx" },
  );

  console.log(
    `Generated ${manifest.product.slug} with ${templateFiles.length} template files using ${manifest.blueprint}.`,
  );
}

await main();