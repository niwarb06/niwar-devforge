import assert from "node:assert/strict";
import test from "node:test";

import { createWebAuthBff } from "../dist/index.js";

function makeBff() {
  let calls = 0;
  const bff = createWebAuthBff({
    backendApiBaseUrl: "https://api.example.test/api/v1",
    publicOrigin: "https://app.example.test",
    fetchImpl: async () => {
      calls += 1;
      return new Response(null, { status: 204 });
    },
  });
  return { bff, getCalls: () => calls };
}

function loginRequest(extraHeaders = {}) {
  return new Request("https://app.example.test/api/auth/session", {
    method: "POST",
    headers: {
      origin: "https://app.example.test",
      "sec-fetch-site": "same-origin",
      "content-type": "application/json",
      ...extraHeaders,
    },
    body: JSON.stringify({
      identifier: "user@example.test",
      password: "correct-horse-battery-staple",
    }),
  });
}

function successfulSessionResponse() {
  return new Response(
    JSON.stringify({
      session_token: "opaque-session-token-123456789",
      expires_in_seconds: 3600,
    }),
    {
      status: 200,
      headers: { "content-type": "application/json" },
    },
  );
}

test("cross-origin logout cannot clear the browser session cookie", async () => {
  const { bff, getCalls } = makeBff();
  const response = await bff.logout(
    new Request("https://app.example.test/api/auth/session", {
      method: "DELETE",
      headers: {
        origin: "https://evil.example.test",
        "sec-fetch-site": "cross-site",
        cookie: "__Host-devforge_session=opaque-session-token-123456789",
      },
    }),
  );

  assert.equal(response.status, 403);
  assert.equal(response.headers.get("set-cookie"), null);
  assert.equal(getCalls(), 0);
});

test("BFF endpoint configuration rejects non-http protocols", () => {
  assert.throws(
    () =>
      createWebAuthBff({
        backendApiBaseUrl: "file:///tmp/api/v1",
        publicOrigin: "https://app.example.test",
      }),
    /backendApiBaseUrl must use http or https/,
  );
});

test("browser-supplied X-Forwarded-For is never relayed by default", async () => {
  let forwardedFor = "not-called";
  const bff = createWebAuthBff({
    backendApiBaseUrl: "https://api.example.test/api/v1",
    publicOrigin: "https://app.example.test",
    fetchImpl: async (_input, init) => {
      forwardedFor = new Headers(init?.headers).get("x-forwarded-for");
      return successfulSessionResponse();
    },
  });

  const response = await bff.login(
    loginRequest({ "x-forwarded-for": "198.51.100.200" }),
  );

  assert.equal(response.status, 200);
  assert.equal(forwardedFor, null);
});

test("explicit trusted client resolver forwards one client IP to the backend", async () => {
  let forwardedFor = null;
  const bff = createWebAuthBff({
    backendApiBaseUrl: "https://api.example.test/api/v1",
    publicOrigin: "https://app.example.test",
    resolveTrustedClientAddress: async () => "198.51.100.42",
    fetchImpl: async (_input, init) => {
      forwardedFor = new Headers(init?.headers).get("x-forwarded-for");
      return successfulSessionResponse();
    },
  });

  const response = await bff.login(loginRequest());

  assert.equal(response.status, 200);
  assert.equal(forwardedFor, "198.51.100.42");
});

test("invalid trusted client resolver output fails closed before backend fetch", async () => {
  let calls = 0;
  const bff = createWebAuthBff({
    backendApiBaseUrl: "https://api.example.test/api/v1",
    publicOrigin: "https://app.example.test",
    resolveTrustedClientAddress: () => "198.51.100.42, 203.0.113.9",
    fetchImpl: async () => {
      calls += 1;
      return successfulSessionResponse();
    },
  });

  const response = await bff.login(loginRequest());

  assert.equal(response.status, 500);
  assert.deepEqual(await response.json(), { code: "bff_internal_error", message: null });
  assert.equal(calls, 0);
});
