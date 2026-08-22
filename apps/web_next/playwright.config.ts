import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "node tests/support/fake-backend.mjs",
      url: "http://127.0.0.1:4101/__test__/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run start -- -p 4100",
      url: "http://127.0.0.1:4100",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
