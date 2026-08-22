import { expect, test, type Page } from "@playwright/test";

const backendControl = "http://127.0.0.1:4101";

async function login(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await page.getByLabel("Email").fill("pilot@example.test");
  await page.getByLabel("Password").fill("correct-horse-battery-staple");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("protected-content")).toBeVisible();
}

test.beforeEach(async ({ request }) => {
  const response = await request.post(`${backendControl}/__test__/reset`);
  expect(response.ok()).toBeTruthy();
});

test("login keeps opaque session out of browser JavaScript and browser-visible JSON", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");

  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign in" }).click();
  const loginResponse = await responsePromise;
  const body = (await loginResponse.json()) as Record<string, unknown>;

  expect(loginResponse.status()).toBe(200);
  expect(body.authenticated).toBe(true);
  expect(body.session_token).toBeUndefined();
  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("profile-email")).toHaveText("pilot@example.test");

  const cookies = await page.context().cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === "devforge_session_pilot");
  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBe(true);
  expect(sessionCookie?.sameSite).toBe("Lax");
  const browserCookieString = await page.evaluate(() => document.cookie);
  expect(browserCookieString).not.toContain("devforge_session_pilot");
  expect(browserCookieString).not.toContain("pilot_session_");
});

test("logout revokes the session and removes protected UI", async ({ page }) => {
  await login(page);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await expect(page.getByTestId("protected-content")).toHaveCount(0);

  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "devforge_session_pilot")).toBe(false);
});

test("back navigation gates restored protected UI until a disabled session is revalidated", async ({
  page,
  request,
}) => {
  await login(page);
  await page.getByRole("link", { name: "Public page" }).click();
  await expect(page).toHaveURL(/\/public$/);

  expect((await request.post(`${backendControl}/__test__/disable-user`)).ok()).toBeTruthy();
  expect(
    (
      await request.post(`${backendControl}/__test__/set-me-delay`, {
        data: { ms: 750 },
      })
    ).ok(),
  ).toBeTruthy();

  await page.goBack({ waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("session-status")).toHaveText("checking", { timeout: 1000 });
  await expect(page.getByTestId("protected-content")).toHaveCount(0);
  await expect(page.getByTestId("protected-gate")).toBeVisible();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous", { timeout: 5000 });
  await expect(page.getByTestId("protected-content")).toHaveCount(0);
});

test("transient upstream failure becomes error without being misclassified as logout", async ({
  page,
  request,
}) => {
  await login(page);
  expect(
    (
      await request.post(`${backendControl}/__test__/set-me-delay`, {
        data: { ms: 300 },
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (
      await request.post(`${backendControl}/__test__/set-me-failure`, {
        data: { enabled: true },
      })
    ).ok(),
  ).toBeTruthy();

  await page.getByRole("button", { name: "Revalidate session" }).click();
  await expect(page.getByTestId("session-status")).toHaveText("checking");
  await expect(page.getByTestId("protected-content")).toHaveCount(0);
  await expect(page.getByTestId("session-status")).toHaveText("error", { timeout: 5000 });
  await expect(page.getByTestId("session-error")).toBeVisible();
});
