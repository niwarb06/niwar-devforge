import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";

const requireFromGeneratedProduct = createRequire(join(process.cwd(), "package.json"));
const { chromium } = requireFromGeneratedProduct("playwright");

const baseURL = process.env.DEVFORGE_STAGING_ORIGIN;
if (!baseURL?.startsWith("https://")) {
  throw new Error("DEVFORGE_STAGING_ORIGIN must be an https origin");
}

const allowInternalCa = process.env.DEVFORGE_STAGING_ALLOW_INTERNAL_CA === "1";
const loginIpLimit = Number.parseInt(
  process.env.DEVFORGE_STAGING_LOGIN_IP_LIMIT ?? process.env.STAGING_LOGIN_IP_LIMIT ?? "3",
  10,
);
if (!Number.isInteger(loginIpLimit) || loginIpLimit < 2 || loginIpLimit > 100) {
  throw new Error("staging login IP limit must be an integer between 2 and 100");
}

const password = "devforge-staging-proof-password";
const email = `staging-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  baseURL,
  ignoreHTTPSErrors: allowInternalCa,
});
const page = await context.newPage();

try {
  await page.goto("/");
  await page.waitForFunction(
    () => document.querySelector('[data-testid="session-status"]')?.textContent === "anonymous",
  );

  await page.getByTestId("email").fill(email);
  await page.getByTestId("password").fill(password);

  const registrationPromise = page.waitForResponse(
    (response) => response.url().endsWith("/api/auth/register") && response.request().method() === "POST",
  );
  await page.getByTestId("register").click();
  const registration = await registrationPromise;
  assert.equal(registration.status(), 201);
  const registrationBody = await registration.json();
  assert.equal(registrationBody.email, email);
  assert.equal(Object.hasOwn(registrationBody, "session_token"), false);

  const loginPromise = page.waitForResponse(
    (response) => response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByTestId("login").click();
  const login = await loginPromise;
  assert.equal(login.status(), 200);
  const loginBody = await login.json();
  assert.equal(loginBody.authenticated, true);
  assert.equal(Object.hasOwn(loginBody, "session_token"), false);

  await page.getByTestId("signed-in-email").waitFor();
  assert.equal(await page.getByTestId("session-status").textContent(), "authenticated");
  assert.equal(await page.getByTestId("signed-in-email").textContent(), email);

  const sessionCookie = (await context.cookies()).find(
    (cookie) => cookie.name === "__Host-devforge_session",
  );
  assert.ok(sessionCookie, "secure __Host- session cookie was not set");
  assert.equal(sessionCookie.httpOnly, true);
  assert.equal(sessionCookie.secure, true);
  assert.equal(sessionCookie.sameSite, "Lax");
  assert.equal(sessionCookie.path, "/");

  const browserState = await page.evaluate(() => ({
    documentCookie: document.cookie,
    localStorageKeys: Object.keys(localStorage),
    sessionStorageKeys: Object.keys(sessionStorage),
    html: document.documentElement.outerHTML,
  }));
  assert.equal(browserState.documentCookie.includes(sessionCookie.value), false);
  assert.deepEqual(browserState.localStorageKeys, []);
  assert.deepEqual(browserState.sessionStorageKeys, []);
  assert.equal(browserState.html.includes(sessionCookie.value), false);

  const me = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me", { credentials: "same-origin", cache: "no-store" });
    return { status: response.status, body: await response.json() };
  });
  assert.equal(me.status, 200);
  assert.equal(me.body.email, email);
  assert.equal(Object.hasOwn(me.body, "session_token"), false);

  const logoutPromise = page.waitForResponse(
    (response) => response.url().endsWith("/api/auth/logout") && response.request().method() === "DELETE",
  );
  await page.getByTestId("logout").click();
  const logout = await logoutPromise;
  assert.equal(logout.status(), 204);
  await page.waitForFunction(
    () => document.querySelector('[data-testid="session-status"]')?.textContent === "anonymous",
  );
  assert.equal(
    (await context.cookies()).some((cookie) => cookie.name === "__Host-devforge_session"),
    false,
  );

  // The successful login above consumes one request in the real client-IP bucket.
  // Each following request attempts to spoof a different ingress address. Correct
  // Caddy overwrite + BFF forwarding keeps all requests in the same real-IP bucket,
  // so the final probe request reaches the configured IP limit and returns 429.
  const spoofProbe = await page.evaluate(async (configuredLoginIpLimit) => {
    const results = [];
    for (let index = 0; index < configuredLoginIpLimit; index += 1) {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: {
          "content-type": "application/json",
          "x-devforge-ingress-client-ip": `198.51.100.${(index % 200) + 10}`,
        },
        body: JSON.stringify({
          identifier: `missing-${Date.now()}-${index}@example.test`,
          password: "wrong-password-value",
        }),
      });
      results.push({ status: response.status, body: await response.json() });
    }
    return results;
  }, loginIpLimit);

  assert.equal(spoofProbe.length, loginIpLimit);
  assert.deepEqual(
    spoofProbe.slice(0, -1).map((result) => result.status),
    Array(loginIpLimit - 1).fill(401),
  );
  assert.equal(spoofProbe.at(-1)?.status, 429);
  assert.equal(spoofProbe.at(-1)?.body.code, "rate_limited");

  console.log("Staging web auth TLS, session, isolation-header and rate-limit proof passed.");
} finally {
  await context.close();
  await browser.close();
}
