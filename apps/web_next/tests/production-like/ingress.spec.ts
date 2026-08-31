import { expect, test } from "@playwright/test";

const password = "devforge-production-like-password";

function uniqueEmail(label: string): string {
  return `production-like-${label}-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;
}

test("TLS ingress sanitizes spoofable forwarding headers and preserves secure browser auth", async ({
  page,
  context,
}) => {
  await page.goto("/");
  expect(new URL(page.url()).protocol).toBe("https:");
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");

  const firstEmail = uniqueEmail("one");
  const attempts = [
    { email: firstEmail, spoofedAddress: "203.0.113.10" },
    { email: uniqueEmail("two"), spoofedAddress: "198.51.100.20" },
    { email: uniqueEmail("three"), spoofedAddress: "192.0.2.30" },
  ];
  const statuses: number[] = [];

  for (const attempt of attempts) {
    const status = await page.evaluate(
      async ({ email, candidatePassword, spoofedAddress }) => {
        const response = await fetch("/api/auth/register", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-forwarded-for": spoofedAddress,
            "x-real-ip": spoofedAddress,
            "x-devforge-ingress-client-ip": spoofedAddress,
            forwarded: `for=${spoofedAddress};proto=http`,
          },
          credentials: "same-origin",
          cache: "no-store",
          body: JSON.stringify({
            email,
            password: candidatePassword,
            display_name: "Production-like Ingress Pilot",
          }),
        });
        return response.status;
      },
      {
        email: attempt.email,
        candidatePassword: password,
        spoofedAddress: attempt.spoofedAddress,
      },
    );
    statuses.push(status);
  }

  expect(statuses).toEqual([201, 201, 429]);

  await page.getByTestId("identifier").fill(firstEmail);
  await page.getByTestId("password").fill(password);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/auth/login") && response.request().method() === "POST",
  );
  await page.getByTestId("login").click();
  const loginResponse = await loginResponsePromise;
  expect(loginResponse.status()).toBe(200);

  const loginBody = await loginResponse.json();
  expect(loginBody.authenticated).toBe(true);
  expect(loginBody).not.toHaveProperty("session_token");

  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("signed-in-email")).toHaveText(firstEmail);

  const cookies = await context.cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === "devforge_pilot_session");
  expect(sessionCookie).toBeTruthy();
  expect(sessionCookie?.httpOnly).toBe(true);
  expect(sessionCookie?.secure).toBe(true);
  expect(sessionCookie?.sameSite).toBe("Lax");

  const browserState = await page.evaluate(() => ({
    documentCookie: document.cookie,
    localStorageKeys: Object.keys(localStorage),
    sessionStorageKeys: Object.keys(sessionStorage),
    html: document.documentElement.outerHTML,
  }));
  expect(browserState.documentCookie).not.toContain("devforge_pilot_session");
  expect(browserState.localStorageKeys).toEqual([]);
  expect(browserState.sessionStorageKeys).toEqual([]);
  expect(browserState.html).not.toContain(sessionCookie?.value ?? "__missing_session_value__");

  await page.goto("/protected");
  await expect(page.getByTestId("session-status")).toHaveText("authenticated");
  await expect(page.getByTestId("protected-secret")).toContainText(firstEmail);

  await page.getByTestId("protected-logout").click();
  await expect(page.getByTestId("session-status")).toHaveText("anonymous");
  expect((await context.cookies()).some((cookie) => cookie.name === "devforge_pilot_session")).toBe(
    false,
  );
});
