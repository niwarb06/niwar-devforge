import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

// These checks protect the Phase-5 host CI recovery contract introduced in PR #77.
// They do not replace real Android/iOS CI jobs or claim simulator coverage.
const repoRoot = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const workflowPath = join(repoRoot, ".github", "workflows", "generator-flutter-auth-ci.yml");

async function workflowStep(name, nextName) {
  const workflow = await readFile(workflowPath, "utf8");
  const start = `      - name: ${name}\n`;
  const next = `\n      - name: ${nextName}`;
  assert.equal(workflow.split(start).length, 2, `${name} must appear exactly once`);
  const remainder = workflow.split(start)[1];
  if (nextName === null) return remainder;
  assert.ok(remainder.includes(next), `${name} must precede ${nextName}`);
  return remainder.split(next)[0];
}

test("Android emulator CI pins, verifies, and bounds NDK installation retries", async () => {
  const step = await workflowStep(
    "Install pinned Android NDK for emulator build",
    "Build generated product in Android emulator host",
  );
  assert.match(step, /set -euo pipefail/);
  assert.match(step, /ndk_version="28\.2\.13676358"/);
  assert.match(step, /for attempt in 1 2 3; do/);
  assert.match(step, /if "\$sdkmanager" --install "ndk;\$ndk_version"/);
  assert.match(step, /test -f "\$ndk_dir\/source\.properties"/);
  assert.match(step, /grep -Eq "\^Pkg\.Revision/);
  assert.match(step, /rm -rf "\$ndk_dir"/);
  assert.match(step, /done\s+exit 1/);
});

test("iOS simulator CI retries startup stalls only, never test failures", async () => {
  const step = await workflowStep(
    "Run iOS Simulator secure-storage integration proof",
    null,
  );
  assert.match(step, /for attempt in \(1, 2\):/);
  assert.match(step, /process\.wait\(timeout=660\)/);
  assert.match(step, /os\.killpg\(process\.pid, signal\.SIGTERM\)/);
  assert.match(step, /if started\.is_set\(\):\s+sys\.exit\("iOS secure-storage test stalled after starting: no retry"\)/);
  assert.match(step, /if attempt == 2:\s+sys\.exit\("iOS test startup stalled twice: failing CI"\)/);
  assert.match(step, /if result != 0:\s+sys\.exit\(result\)/);
  assert.match(step, /if not started\.is_set\(\):\s+sys\.exit\("Flutter exited successfully without evidence of test execution"\)/);
});
