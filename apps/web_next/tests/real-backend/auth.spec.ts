import { expect, test } from "@playwright/test";

const password = "devforge-real-backend-password";

function uniqueEmail(): string {
  return `real-backend-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;
}

test("real FastAPI/Postgres/Redis auth works through the browser BFF without token exposure", async ({
  page,
  context,
}) => {
  const email = uniqueEmail();

  await page.goto("/");
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");

  const registration = await page.evaluate(
    async ({ email: candidateEmail, password: candidatePassword }) => {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "content-type": "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({
          email: candidateEmail,
          password: candidatePassword,
          display_name: "Real Backend Pilot",
        }),
      });
      return {
        status: response.status,
        body: await response.json(),
      };
    },
    { email, password },
  );

  expect(registration.status).toBe(201);
  expect(registration.body.email).toBe(email);
  expect(registration.body.display_name).toBe("Real Backend Pilot");
  expect(registration.body).not.toHaveProperty("session_token");

  await page.getByTestId("identifier").fill(email);
  await page.getByTestId("password").fill(password);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByTestId("login").click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status()).toBe(200);
  const browserLoginBody = await loginResponse.json();
  expect(browserLoginBody.authenticated).toBe(true);
  expect(browserLoginBody).not.toHaveProperty("session_token");

  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("signed-in-email")).toHaveText(email);

  const cookies = await context.cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === "devforge_pilot_session");
  expect(sessionCookie).toBeTruthy();
  expect(sessionCookie?.httpOnly).toBe(true);
  expect(sessionCookie?.sameSite).toBe("Lax");

  const browserStorage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
    documentCookie: document.cookie,
    html: document.documentElement.outerHTML,
  }));
  expect(browserStorage.local).toEqual([]);
  expect(browserStorage.session).toEqual([]);
  expect(browserStorage.documentCookie).not.toContain("devforge_pilot_session");
  expect(browserStorage.html).not.toContain(sessionCookie?.value ?? "__missing_session_value__");

  const simulatorStatus = await page.evaluate(async () => {
    const response = await fetch("/api/pilot-backend/v1/users/me", {
      cache: "no-store",
      credentials: "same-origin",
    });
    return response.status;
  });
  expect(simulatorStatus).toBe(404);

  const profileUpdate = await page.evaluate(async () => {
    const response = await fetch("/api/auth/profile", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      credentials: "same-origin",
      cache: "no-store",
      body: JSON.stringify({ display_name: "Updated Through Real Backend" }),
    });
    return { status: response.status, body: await response.json() };
  });
  expect(profileUpdate.status).toBe(200);
  expect(profileUpdate.body.display_name).toBe("Updated Through Real Backend");
  expect(profileUpdate.body).not.toHaveProperty("session_token");

  const currentProfile = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me", {
      cache: "no-store",
      credentials: "same-origin",
    });
    return { status: response.status, body: await response.json() };
  });
  expect(currentProfile.status).toBe(200);
  expect(currentProfile.body.email).toBe(email);
  expect(currentProfile.body.display_name).toBe("Updated Through Real Backend");
  expect(currentProfile.body).not.toHaveProperty("session_token");

  await page.goto("/protected");
  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("protected-secret")).toContainText(email);

  await page.getByTestId("protected-logout").click();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  await expect(page.getByTestId("protected-secret")).toHaveCount(0);

  const afterLogout = await page.evaluate(async () => {
    const response = await fetch("/api/auth/me", {
      cache: "no-store",
      credentials: "same-origin",
    });
    return response.status;
  });
  expect(afterLogout).toBe(401);
  expect((await context.cookies()).some((cookie) => cookie.name === "devforge_pilot_session")).toBe(
    false,
  );
});
