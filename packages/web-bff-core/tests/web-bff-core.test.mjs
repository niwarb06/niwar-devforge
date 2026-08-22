import assert from "node:assert/strict";
import test from "node:test";

import { createWebAuthBff } from "../dist/index.js";

function jsonResponse(status, body, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

function createHarness(responses) {
  const calls = [];
  const queue = [...responses];
  const fetchImpl = async (input, init = {}) => {
    calls.push({ input: String(input), init });
    const next = queue.shift();
    if (!next) throw new Error("unexpected fetch");
    return typeof next === "function" ? next(input, init) : next;
  };
  const bff = createWebAuthBff({
    backendApiBaseUrl: "https://api.example.test/api/v1",
    publicOrigin: "https://app.example.test",
    fetchImpl,
  });
  return { bff, calls };
}

function jsonRequest(path, method, body, extraHeaders = {}) {
  return new Request(`https://app.example.test${path}`, {
    method,
    headers: {
      origin: "https://app.example.test",
      "sec-fetch-site": "same-origin",
      "content-type": "application/json",
      ...extraHeaders,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

test("login stores the opaque backend token only in a Secure HttpOnly cookie", async () => {
  const token = "opaque-secret-session-token-123456789";
  const { bff } = createHarness([
    jsonResponse(200, { session_token: token, token_type: "bearer", expires_in_seconds: 3600 }),
  ]);

  const response = await bff.login(
    jsonRequest("/api/auth/session", "POST", {
      identifier: "user@example.test",
      password: "password-value",
    }),
  );

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-store");
  const cookie = response.headers.get("set-cookie");
  assert.ok(cookie);
  assert.match(cookie, /__Host-devforge_session=/);
  assert.match(cookie, /HttpOnly/);
  assert.match(cookie, /Secure/);
  assert.match(cookie, /SameSite=Lax/);
  assert.match(cookie, /Path=\//);
  assert.doesNotMatch(await response.text(), new RegExp(token));
});

test("cross-origin credential requests are rejected before the backend is called", async () => {
  const { bff, calls } = createHarness([]);
  const request = new Request("https://app.example.test/api/auth/session", {
    method: "POST",
    headers: {
      origin: "https://evil.example.test",
      "sec-fetch-site": "cross-site",
      "content-type": "application/json",
    },
    body: JSON.stringify({ identifier: "user@example.test", password: "password-value" }),
  });

  const response = await bff.login(request);

  assert.equal(response.status, 403);
  assert.deepEqual(await response.json(), { code: "same_origin_required", message: null });
  assert.equal(calls.length, 0);
});

test("authenticated profile reads use the cookie server-side as a bearer credential", async () => {
  const token = "opaque-profile-session-token-123456789";
  const { bff, calls } = createHarness([
    jsonResponse(200, {
      user_id: "18d33f39-583a-40ee-b1b1-65a18da3aa25",
      email: "user@example.test",
      display_name: "User",
      is_active: true,
    }),
  ]);

  const response = await bff.me(
    new Request("https://app.example.test/api/auth/me", {
      headers: { cookie: `__Host-devforge_session=${encodeURIComponent(token)}` },
    }),
  );

  assert.equal(response.status, 200);
  assert.equal(calls.length, 1);
  const headers = new Headers(calls[0].init.headers);
  assert.equal(headers.get("authorization"), `Bearer ${token}`);
  assert.equal(calls[0].input, "https://api.example.test/api/v1/users/me");
});

test("stale backend sessions clear the browser cookie", async () => {
  const token = "opaque-stale-session-token-123456789";
  const { bff } = createHarness([
    jsonResponse(401, { code: "not_authenticated", message: null }),
  ]);

  const response = await bff.me(
    new Request("https://app.example.test/api/auth/me", {
      headers: { cookie: `__Host-devforge_session=${encodeURIComponent(token)}` },
    }),
  );

  assert.equal(response.status, 401);
  const cookie = response.headers.get("set-cookie");
  assert.ok(cookie);
  assert.match(cookie, /Max-Age=0/);
  assert.match(cookie, /HttpOnly/);
  assert.match(cookie, /Secure/);
});

test("logout revokes the backend session and clears the browser cookie", async () => {
  const token = "opaque-logout-session-token-123456789";
  const { bff, calls } = createHarness([new Response(null, { status: 204 })]);

  const response = await bff.logout(
    new Request("https://app.example.test/api/auth/session", {
      method: "DELETE",
      headers: {
        origin: "https://app.example.test",
        "sec-fetch-site": "same-origin",
        cookie: `__Host-devforge_session=${encodeURIComponent(token)}`,
      },
    }),
  );

  assert.equal(response.status, 204);
  const headers = new Headers(calls[0].init.headers);
  assert.equal(headers.get("authorization"), `Bearer ${token}`);
  assert.match(response.headers.get("set-cookie") ?? "", /Max-Age=0/);
});

test("__Host- cookies cannot be configured without Secure", () => {
  assert.throws(
    () =>
      createWebAuthBff({
        backendApiBaseUrl: "https://api.example.test/api/v1",
        publicOrigin: "http://localhost:3000",
        secureCookie: false,
      }),
    /__Host- cookies require secureCookie=true/,
  );
});

test("unsafe JSON bodies are bounded and content typed", async () => {
  const { bff, calls } = createHarness([]);
  const response = await bff.register(
    new Request("https://app.example.test/api/auth/register", {
      method: "POST",
      headers: {
        origin: "https://app.example.test",
        "sec-fetch-site": "same-origin",
        "content-type": "text/plain",
      },
      body: "not-json",
    }),
  );

  assert.equal(response.status, 415);
  assert.equal(calls.length, 0);
});
