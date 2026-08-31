import { defineConfig, devices } from "@playwright/test";

const publicOrigin =
  process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN ?? "https://127.0.0.1:3443";
const backendOrigin = process.env.DEVFORGE_REAL_BACKEND_ORIGIN ?? "http://127.0.0.1:8000";
const databaseUrl =
  process.env.DEVFORGE_DATABASE_URL ??
  "postgresql+psycopg://devforge@127.0.0.1:5432/devforge";
const redisUrl = process.env.DEVFORGE_REDIS_URL ?? "redis://127.0.0.1:6379/0";

export default defineConfig({
  testDir: "./tests/production-like",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: publicOrigin,
    ignoreHTTPSErrors: true,
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
        DEVFORGE_TRUSTED_PROXY_CIDRS: '["127.0.0.1/32"]',
        DEVFORGE_REGISTER_IP_LIMIT: "2",
        DEVFORGE_REGISTER_IDENTIFIER_LIMIT: "20",
      },
    },
    {
      command: "npm run start -- -H 127.0.0.1 -p 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NODE_ENV: "production",
        DEVFORGE_PILOT_PUBLIC_ORIGIN: publicOrigin,
        DEVFORGE_PILOT_BACKEND_API_BASE_URL: `${backendOrigin}/api/v1`,
        DEVFORGE_PILOT_TRUST_INGRESS_CLIENT_IP: "1",
      },
    },
    {
      command: "node ./scripts/production-like-ingress.mjs",
      url: `${publicOrigin}/_devforge_ingress_health`,
      reuseExistingServer: false,
      timeout: 120_000,
      ignoreHTTPSErrors: true,
    },
  ],
  projects: [
    {
      name: "chromium-production-like-ingress",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
