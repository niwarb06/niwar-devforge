import { readFile } from "node:fs/promises";
import { dirname, isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";

const generatorRoot = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = dirname(generatorRoot);
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

const BLUEPRINT_MODULES = Object.freeze({
  "web-next-auth": Object.freeze(["web-bff-core", "web-session-core"]),
  "flutter-mobile-auth": Object.freeze(["flutter-auth-core"]),
});

const PACK_CONTRACTS = Object.freeze({
  business: "packs/business/business-pack-contract.json",
  booking: "packs/booking/booking-pack-contract.json",
  marketplace: "packs/marketplace/marketplace-pack-contract.json",
  "dating-social": "packs/dating-social/dating-social-pack-contract.json",
  "delivery-logistics": "packs/delivery-logistics/delivery-logistics-pack-contract.json",
  ai_saas: "packs/ai_saas/ai_saas-pack-contract.json",
});

function fail(message) {
  throw new Error(`DevForge generation record: ${message}`);
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function assertPlainObject(value, label) {
  if (!isPlainObject(value)) fail(`${label} must be an object`);
}

function assertExactKeys(value, expected, label) {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail(`${label} keys must equal ${JSON.stringify(wanted)}`);
  }
}

function assertNonEmptyString(value, label) {
  if (typeof value !== "string" || value.length === 0) {
    fail(`${label} must be a non-empty string`);
  }
}

function assertExactStringArray(value, expected, label) {
  if (!Array.isArray(value) || value.length !== expected.length) {
    fail(`${label} must equal ${JSON.stringify(expected)}`);
  }
  for (let index = 0; index < expected.length; index += 1) {
    if (value[index] !== expected[index]) {
      fail(`${label} must equal ${JSON.stringify(expected)}`);
    }
  }
}

function assertSafeVendorDestination(value, label) {
  if (
    typeof value !== "string" ||
    !value.startsWith("vendor/") ||
    isAbsolute(value) ||
    value.includes("\\") ||
    value.split("/").some((part) => !part || part === "." || part === "..")
  ) {
    fail(`${label} must be a safe vendor/ path`);
  }
}

async function validatePack(pack) {
  assertPlainObject(pack, "pack");
  assertExactKeys(pack, new Set(["name", "schema_version", "capabilities"]), "pack");
  if (typeof pack.name !== "string" || !(pack.name in PACK_CONTRACTS)) {
    fail(`pack.name must be one of ${JSON.stringify(Object.keys(PACK_CONTRACTS))}`);
  }
  if (pack.schema_version !== 1) fail("pack.schema_version must equal 1");

  const contract = JSON.parse(
    await readFile(join(repositoryRoot, PACK_CONTRACTS[pack.name]), "utf8"),
  );
  assertPlainObject(contract, `pack contract ${pack.name}`);
  assertExactKeys(
    contract,
    new Set(["schema_version", "pack", "capabilities"]),
    `pack contract ${pack.name}`,
  );
  if (contract.schema_version !== 1 || contract.pack !== pack.name) {
    fail(`pack contract ${pack.name} does not match the generation record`);
  }
  assertExactStringArray(pack.capabilities, contract.capabilities, "pack.capabilities");
}

export async function validateGenerationRecord(record) {
  assertPlainObject(record, "record");
  const allowedKeys = new Set([
    "schema_version",
    "generator",
    "generator_version",
    "blueprint",
    "product",
    "modules",
    "package_specs",
    "pack",
    "dependency_mode",
    "vendored_packages",
  ]);
  for (const key of Object.keys(record)) {
    if (!allowedKeys.has(key)) fail(`record contains unsupported key ${JSON.stringify(key)}`);
  }
  for (const key of [
    "schema_version",
    "generator",
    "generator_version",
    "blueprint",
    "product",
    "modules",
    "package_specs",
    "dependency_mode",
  ]) {
    if (!(key in record)) fail(`record is missing required key ${JSON.stringify(key)}`);
  }

  if (record.schema_version !== 1) fail("schema_version must equal 1");
  if (record.generator !== "niwar-devforge") fail('generator must equal "niwar-devforge"');
  if (record.generator_version !== "0.5.0") fail('generator_version must equal "0.5.0"');
  if (typeof record.blueprint !== "string" || !(record.blueprint in BLUEPRINT_MODULES)) {
    fail(`blueprint must be one of ${JSON.stringify(Object.keys(BLUEPRINT_MODULES))}`);
  }

  assertPlainObject(record.product, "product");
  assertExactKeys(record.product, new Set(["slug", "display_name", "package_name"]), "product");
  assertNonEmptyString(record.product.slug, "product.slug");
  assertNonEmptyString(record.product.display_name, "product.display_name");
  assertNonEmptyString(record.product.package_name, "product.package_name");

  const expectedModules = BLUEPRINT_MODULES[record.blueprint];
  assertExactStringArray(record.modules, expectedModules, "modules");
  assertPlainObject(record.package_specs, "package_specs");
  assertExactKeys(record.package_specs, new Set(expectedModules), "package_specs");
  for (const moduleName of expectedModules) {
    assertNonEmptyString(record.package_specs[moduleName], `package_specs.${moduleName}`);
  }

  if (record.pack !== undefined) await validatePack(record.pack);

  if (!new Set(["manifest-specs", "verified-vendored-bundle"]).has(record.dependency_mode)) {
    fail("dependency_mode is invalid");
  }
  if (record.dependency_mode === "manifest-specs") {
    if (record.vendored_packages !== undefined) {
      fail("vendored_packages is forbidden when dependency_mode is manifest-specs");
    }
  } else {
    assertPlainObject(record.vendored_packages, "vendored_packages");
    assertExactKeys(record.vendored_packages, new Set(expectedModules), "vendored_packages");
    for (const moduleName of expectedModules) {
      const item = record.vendored_packages[moduleName];
      assertPlainObject(item, `vendored_packages.${moduleName}`);
      assertExactKeys(
        item,
        new Set(["destination", "sha256"]),
        `vendored_packages.${moduleName}`,
      );
      assertSafeVendorDestination(item.destination, `vendored_packages.${moduleName}.destination`);
      if (typeof item.sha256 !== "string" || !SHA256_PATTERN.test(item.sha256)) {
        fail(`vendored_packages.${moduleName}.sha256 must be lowercase SHA-256`);
      }
      const packageSpec = record.package_specs[moduleName];
      if (packageSpec !== item.destination && packageSpec !== `file:${item.destination}`) {
        fail(`package_specs.${moduleName} must reference its vendored destination`);
      }
    }
  }

  return record;
}

async function main() {
  if (process.argv.length !== 3) {
    fail("usage: node generator/validate-generation-record.mjs <record.json>");
  }
  const record = JSON.parse(await readFile(process.argv[2], "utf8"));
  await validateGenerationRecord(record);
  console.log("DevForge generation record valid.");
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  await main();
}
