import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN ?? "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run start -- -H 127.0.0.1 -p 3000",
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      NODE_ENV: "production",
      DEVFORGE_PILOT_INPROCESS_BACKEND: "1",
      DEVFORGE_PILOT_TEST_CONTROL: "1",
      DEVFORGE_PILOT_PUBLIC_ORIGIN: baseURL,
      DEVFORGE_PILOT_BACKEND_API_BASE_URL: `${baseURL}/api/pilot-backend/v1`,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
