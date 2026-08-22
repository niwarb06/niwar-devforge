import { defineConfig, devices } from "@playwright/test";

const publicOrigin = process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN ?? "http://127.0.0.1:3000";
const backendOrigin = process.env.DEVFORGE_REAL_BACKEND_ORIGIN ?? "http://127.0.0.1:8000";
const databaseUrl =
  process.env.DEVFORGE_DATABASE_URL ??
  "postgresql+psycopg://devforge@127.0.0.1:5432/devforge";
const redisUrl = process.env.DEVFORGE_REDIS_URL ?? "redis://127.0.0.1:6379/0";

export default defineConfig({
  testDir: "./tests/real-backend",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: publicOrigin,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python -m uvicorn devforge_core.main:app --host 127.0.0.1 --port 8000",
      cwd: "../../packages/backend-core",
      url: `${backendOrigin}/api/v1/health/live`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DEVFORGE_ENVIRONMENT: "test",
        DEVFORGE_DATABASE_URL: databaseUrl,
        DEVFORGE_REDIS_URL: redisUrl,
      },
    },
    {
      command: "npm run start -- -H 127.0.0.1 -p 3000",
      url: publicOrigin,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NODE_ENV: "production",
        DEVFORGE_PILOT_PUBLIC_ORIGIN: publicOrigin,
        DEVFORGE_PILOT_BACKEND_API_BASE_URL: `${backendOrigin}/api/v1`,
      },
    },
  ],
  projects: [
    {
      name: "chromium-real-backend",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
