import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";

const CONTROL_HEADERS = { "x-devforge-pilot-control": "pilot-e2e" };

async function resetPilot(request: APIRequestContext) {
  const response = await request.post("/api/pilot-control", {
    headers: CONTROL_HEADERS,
    data: { action: "reset" },
  });
  expect(response.ok()).toBeTruthy();
}

async function login(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await page.getByTestId("identifier").fill("pilot@example.test");
  await page.getByTestId("password").fill("devforge-pilot-password");

  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByTestId("login").click();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const body = (await response.json()) as Record<string, unknown>;
  expect(body.authenticated).toBe(true);
  expect(body).not.toHaveProperty("session_token");
  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  return body;
}

test.beforeEach(async ({ request }) => {
  await resetPilot(request);
});

test("login keeps the opaque session out of browser JavaScript", async ({ page, context }) => {
  await login(page);

  const cookies = await context.cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === "devforge_pilot_session");
  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBe(true);
  expect(sessionCookie?.sameSite).toBe("Lax");

  const browserState = await page.evaluate(() => ({
    documentCookie: document.cookie,
    localStorage: Object.entries(localStorage),
    sessionStorage: Object.entries(sessionStorage),
    html: document.documentElement.outerHTML,
  }));

  expect(browserState.documentCookie).not.toContain("devforge_pilot_session");
  expect(browserState.localStorage).toEqual([]);
  expect(browserState.sessionStorage).toEqual([]);
  if (sessionCookie) expect(browserState.html).not.toContain(sessionCookie.value);

  await page.getByRole("link", { name: "Protected page" }).click();
  await expect(page).toHaveURL(/\/protected$/);
  await expect(page.getByTestId("protected-secret")).toBeVisible();
});

test("back navigation after server revocation does not trust restored protected content", async ({
  page,
  request,
}) => {
  await login(page);
  await page.goto("/protected");
  await expect(page.getByTestId("protected-secret")).toBeVisible();

  await page.getByRole("link", { name: "Leave protected page" }).click();
  await expect(page).toHaveURL(/\/public$/);

  const revoke = await request.post("/api/pilot-control", {
    headers: CONTROL_HEADERS,
    data: { action: "revoke" },
  });
  expect(revoke.ok()).toBeTruthy();

  await page.goBack({ waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(/\/protected$/);
  await expect(page.getByTestId("protected-secret")).not.toBeVisible();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await expect(page.getByTestId("protected-anonymous")).toBeVisible();
  await expect(page.getByTestId("session-source")).toHaveText(/bfcache|pageshow|start|visible/);
});

test("logout revokes the server session and closes the protected UI gate", async ({
  page,
  context,
}) => {
  await login(page);
  await page.goto("/protected");
  await expect(page.getByTestId("protected-secret")).toBeVisible();

  await page.getByTestId("protected-logout").click();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await expect(page.getByTestId("protected-secret")).not.toBeVisible();

  const cookies = await context.cookies();
  expect(cookies.some((cookie) => cookie.name === "devforge_pilot_session")).toBe(false);
});

test("disabled user is rejected on a fresh browser session check", async ({ page, request }) => {
  await login(page);
  await page.goto("/protected");
  await expect(page.getByTestId("protected-secret")).toBeVisible();

  const disable = await request.post("/api/pilot-control", {
    headers: CONTROL_HEADERS,
    data: { action: "disable" },
  });
  expect(disable.ok()).toBeTruthy();

  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
  });

  await expect(page.getByTestId("protected-secret")).not.toBeVisible();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await expect(page.getByTestId("session-source")).toHaveText("bfcache");
});
