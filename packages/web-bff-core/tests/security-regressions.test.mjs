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
