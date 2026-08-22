import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join } from "node:path";

const requireFromGeneratedProduct = createRequire(join(process.cwd(), "package.json"));
const { chromium } = requireFromGeneratedProduct("playwright");

const baseURL = process.env.DEVFORGE_GENERATED_RUNTIME_ORIGIN ?? "http://127.0.0.1:3000";
const password = "devforge-generated-runtime-password";
const email = `generated-runtime-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;

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

  const registrationResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/register") && response.request().method() === "POST",
  );
  await page.getByTestId("register").click();
  const registrationResponse = await registrationResponsePromise;
  assert.equal(registrationResponse.status(), 201);
  const registrationBody = await registrationResponse.json();
  assert.equal(registrationBody.email, email);
  assert.equal(Object.hasOwn(registrationBody, "session_token"), false);
  await page.getByTestId("message").waitFor();
  assert.equal(await page.getByTestId("message").textContent(), "registered");

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByTestId("login").click();
  const loginResponse = await loginResponsePromise;
  assert.equal(loginResponse.status(), 200);
  const loginBody = await loginResponse.json();
  assert.equal(loginBody.authenticated, true);
  assert.equal(Object.hasOwn(loginBody, "session_token"), false);

  await page.getByTestId("signed-in-email").waitFor();
  assert.equal(await page.getByTestId("session-status").textContent(), "authenticated");
  assert.equal(await page.getByTestId("signed-in-email").textContent(), email);

  const cookies = await context.cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === "devforge_session");
  assert.ok(sessionCookie, "generated product session cookie was not set");
  assert.equal(sessionCookie.httpOnly, true);
  assert.equal(sessionCookie.sameSite, "Lax");

  const browserState = await page.evaluate(() => ({
    documentCookie: document.cookie,
    localStorageKeys: Object.keys(localStorage),
    sessionStorageKeys: Object.keys(sessionStorage),
    html: document.documentElement.outerHTML,
  }));
  assert.equal(browserState.documentCookie.includes("devforge_session"), false);
  assert.deepEqual(browserState.localStorageKeys, []);
  assert.deepEqual(browserState.sessionStorageKeys, []);
  assert.equal(browserState.html.includes(sessionCookie.value), false);

  const me = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me", {
      credentials: "same-origin",
      cache: "no-store",
    });
    return { status: response.status, body: await response.json() };
  });
  assert.equal(me.status, 200);
  assert.equal(me.body.email, email);
  assert.equal(Object.hasOwn(me.body, "session_token"), false);

  const logoutResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/logout") && response.request().method() === "DELETE",
  );
  await page.getByTestId("logout").click();
  const logoutResponse = await logoutResponsePromise;
  assert.equal(logoutResponse.status(), 204);
  await page.waitForFunction(
    () => document.querySelector('[data-testid="session-status"]')?.textContent === "anonymous",
  );

  const cookiesAfterLogout = await context.cookies();
  assert.equal(cookiesAfterLogout.some((cookie) => cookie.name === "devforge_session"), false);

  const afterLogoutStatus = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me", {
      credentials: "same-origin",
      cache: "no-store",
    });
    return response.status;
  });
  assert.equal(afterLogoutStatus, 401);

  console.log("Generated web-auth runtime E2E passed.");
} finally {
  await context.close();
  await browser.close();
}
