#!/usr/bin/env node

import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const GENERATOR_VERSION = "0.1.0";
const BLUEPRINT = "web-next-auth";
const BLUEPRINT_MODULES = ["web-bff-core", "web-session-core"];
const TOKEN_PATTERN = /\{\{([A-Z0-9_]+)\}\}/g;
const SLUG_PATTERN = /^[a-z][a-z0-9-]{1,47}[a-z0-9]$/;
const PACKAGE_PATTERN = /^@[a-z0-9][a-z0-9._-]*\/[a-z0-9][a-z0-9._-]*$/;
const SAFE_PACKAGE_SPEC_PATTERN = /^(?:file:\.{1,2}\/|[~^]?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\S*$/;

const generatorRoot = dirname(fileURLToPath(import.meta.url));
const templatePath = join(generatorRoot, "templates", BLUEPRINT, "files.json");

function fail(message) {
  throw new Error(`DevForge generator: ${message}`);
}

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
  if (value.blueprint !== BLUEPRINT) fail(`blueprint must equal ${BLUEPRINT}`);

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
    !PACKAGE_PATTERN.test(value.product.package_name)
  ) {
    fail("product.package_name must be a lowercase scoped npm package name");
  }

  if (
    !Array.isArray(value.modules) ||
    value.modules.length !== BLUEPRINT_MODULES.length ||
    !BLUEPRINT_MODULES.every((moduleName, index) => value.modules[index] === moduleName)
  ) {
    fail(`modules must equal ${JSON.stringify(BLUEPRINT_MODULES)}`);
  }

  assertPlainObject(value.package_specs, "package_specs");
  assertExactKeys(value.package_specs, new Set(BLUEPRINT_MODULES), "package_specs");
  for (const moduleName of BLUEPRINT_MODULES) {
    const spec = value.package_specs[moduleName];
    if (typeof spec !== "string" || !SAFE_PACKAGE_SPEC_PATTERN.test(spec) || /[\r\n\0]/.test(spec)) {
      fail(`package_specs.${moduleName} is not an allowed package spec`);
    }
  }

  return value;
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
  const manifest = validateManifest(JSON.parse(await readFile(manifestPath, "utf8")));
  const templateFiles = validateTemplateFiles(JSON.parse(await readFile(templatePath, "utf8")));

  await ensureEmptyOutput(outputRoot);
  await mkdir(outputRoot, { recursive: true });

  const tokens = {
    PRODUCT_NAME: manifest.product.display_name,
    PRODUCT_SLUG: manifest.product.slug,
    PACKAGE_NAME: manifest.product.package_name,
    WEB_BFF_SPEC: manifest.package_specs["web-bff-core"],
    WEB_SESSION_SPEC: manifest.package_specs["web-session-core"],
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
    blueprint: BLUEPRINT,
    product: manifest.product,
    modules: manifest.modules,
    package_specs: manifest.package_specs,
  };
  await writeFile(
    join(outputRoot, ".devforge-generation.json"),
    `${JSON.stringify(generationRecord, null, 2)}\n`,
    { encoding: "utf8", flag: "wx" },
  );

  console.log(`Generated ${manifest.product.slug} with ${templateFiles.length} template files.`);
}

await main();
