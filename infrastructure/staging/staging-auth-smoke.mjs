import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";

const requireFromHarness = createRequire(join(process.cwd(), "package.json"));
const { chromium } = requireFromHarness("playwright");

const baseURL = process.env.DEVFORGE_STAGING_ORIGIN;
if (!baseURL?.startsWith("https://")) {
  throw new Error("DEVFORGE_STAGING_ORIGIN must be an https origin");
}

const password = "devforge-staging-smoke-password";
const email = `rollback-smoke-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ baseURL });
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

  console.log("Real staging rollback auth smoke passed.");
} finally {
  await context.close();
  await browser.close();
}
