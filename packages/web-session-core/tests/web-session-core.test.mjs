import assert from "node:assert/strict";
import test from "node:test";

import { createWebSessionMonitor } from "../dist/index.js";

class FakeTarget {
  #listeners = new Map();

  addEventListener(type, listener) {
    const listeners = this.#listeners.get(type) ?? new Set();
    listeners.add(listener);
    this.#listeners.set(type, listeners);
  }

  removeEventListener(type, listener) {
    this.#listeners.get(type)?.delete(listener);
  }

  dispatch(type, event = {}) {
    for (const listener of this.#listeners.get(type) ?? []) {
      listener({ type, ...event });
    }
  }
}

class FakeVisibility extends FakeTarget {
  visibilityState = "hidden";
}

const flush = async () => {
  await new Promise((resolve) => setTimeout(resolve, 0));
};

const jsonResponse = (value, init = {}) =>
  new Response(JSON.stringify(value), {
    status: 200,
    headers: { "content-type": "application/json" },
    ...init,
  });

test("rejects non-relative or secret-bearing session endpoints", () => {
  for (const endpoint of [
    "https://evil.example/api/auth/me",
    "//evil.example/api/auth/me",
    "/api/auth/me?token=secret",
    "/api/auth/me#fragment",
    "/api\\auth\\me",
  ]) {
    assert.throws(
      () =>
        createWebSessionMonitor({
          endpoint,
          fetchImpl: async () => jsonResponse({ user_id: "1" }),
          onChange() {},
        }),
      /same-origin path/,
    );
  }
});

test("start revalidates through the same-origin BFF without bearer access", async () => {
  const requests = [];
  const snapshots = [];
  const eventTarget = new FakeTarget();
  const visibilitySource = new FakeVisibility();

  const monitor = createWebSessionMonitor({
    eventTarget,
    visibilitySource,
    now: () => 1234,
    fetchImpl: async (input, init) => {
      requests.push({ input, init });
      return jsonResponse({ user_id: "u1", email: "user@example.test" });
    },
    onChange(snapshot) {
      snapshots.push(snapshot);
    },
  });

  monitor.start();
  assert.equal(monitor.current().status, "checking");
  await flush();

  assert.equal(requests.length, 1);
  assert.equal(requests[0].input, "/api/auth/me");
  assert.equal(requests[0].init.method, "GET");
  assert.equal(requests[0].init.credentials, "same-origin");
  assert.equal(requests[0].init.cache, "no-store");
  assert.equal(requests[0].init.redirect, "error");
  assert.deepEqual(requests[0].init.headers, { accept: "application/json" });
  assert.equal("authorization" in requests[0].init.headers, false);

  assert.equal(snapshots[0].status, "checking");
  assert.equal(monitor.current().status, "authenticated");
  assert.equal(monitor.current().profile.user_id, "u1");
  assert.equal(monitor.current().checkedAtMs, 1234);
});

test("401 becomes anonymous while transient upstream failure does not", async () => {
  let response = new Response(null, { status: 401 });
  const monitor = createWebSessionMonitor({
    revalidateOnStart: false,
    fetchImpl: async () => response,
    onChange() {},
  });

  let snapshot = await monitor.revalidate();
  assert.equal(snapshot.status, "anonymous");
  assert.equal(snapshot.errorCode, null);

  response = new Response(null, { status: 503 });
  snapshot = await monitor.revalidate();
  assert.equal(snapshot.status, "error");
  assert.equal(snapshot.errorCode, "session_revalidation_failed");
});

test("BFCache pageshow gates stale UI synchronously and then resolves fresh state", async () => {
  const eventTarget = new FakeTarget();
  const visibilitySource = new FakeVisibility();
  const snapshots = [];
  let requestCount = 0;

  const monitor = createWebSessionMonitor({
    eventTarget,
    visibilitySource,
    fetchImpl: async () => {
      requestCount += 1;
      if (requestCount === 1) {
        return jsonResponse({ user_id: "u1" });
      }
      return new Response(null, { status: 401 });
    },
    onChange(snapshot) {
      snapshots.push(snapshot);
    },
  });

  monitor.start();
  await flush();
  assert.equal(monitor.current().status, "authenticated");

  eventTarget.dispatch("pageshow", { persisted: true });
  assert.equal(monitor.current().status, "checking");
  assert.equal(monitor.current().source, "bfcache");
  assert.equal(monitor.current().profile, null);
  await flush();

  const bfcacheChecking = snapshots.find(
    (snapshot) => snapshot.status === "checking" && snapshot.source === "bfcache",
  );
  assert.ok(bfcacheChecking);
  assert.equal(monitor.current().status, "anonymous");
  assert.equal(monitor.current().source, "bfcache");
});

test("visibility revalidation runs only when the document becomes visible", async () => {
  const eventTarget = new FakeTarget();
  const visibilitySource = new FakeVisibility();
  let requests = 0;

  const monitor = createWebSessionMonitor({
    eventTarget,
    visibilitySource,
    revalidateOnStart: false,
    fetchImpl: async () => {
      requests += 1;
      return jsonResponse({ user_id: "u1" });
    },
    onChange() {},
  });

  monitor.start();
  visibilitySource.dispatch("visibilitychange");
  await flush();
  assert.equal(requests, 0);

  visibilitySource.visibilityState = "visible";
  visibilitySource.dispatch("visibilitychange");
  assert.equal(monitor.current().status, "checking");
  await flush();
  assert.equal(requests, 1);
  assert.equal(monitor.current().source, "visible");
});

test("newer auth-change revalidation cannot be overwritten by an older request", async () => {
  let resolveFirst;
  const first = new Promise((resolve) => {
    resolveFirst = resolve;
  });
  let call = 0;

  const monitor = createWebSessionMonitor({
    revalidateOnStart: false,
    fetchImpl: async () => {
      call += 1;
      if (call === 1) {
        return first;
      }
      return new Response(null, { status: 401 });
    },
    onChange() {},
  });

  const oldRequest = monitor.revalidate("manual");
  const freshRequest = monitor.revalidate("auth-change");
  await freshRequest;
  assert.equal(monitor.current().status, "anonymous");
  assert.equal(monitor.current().source, "auth-change");

  resolveFirst(jsonResponse({ user_id: "stale-user" }));
  await oldRequest;
  assert.equal(monitor.current().status, "anonymous");
  assert.equal(monitor.current().source, "auth-change");
});

test("oversized or invalid profile bodies fail with a sanitized state", async () => {
  const monitor = createWebSessionMonitor({
    revalidateOnStart: false,
    maxResponseBytes: 1024,
    fetchImpl: async () =>
      new Response(JSON.stringify({ data: "x".repeat(2048) }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    onChange() {},
  });

  const snapshot = await monitor.revalidate();
  assert.equal(snapshot.status, "error");
  assert.equal(snapshot.errorCode, "session_revalidation_failed");
  assert.equal(snapshot.profile, null);
});

test("stop removes history and visibility listeners and aborts lifecycle activity", async () => {
  const eventTarget = new FakeTarget();
  const visibilitySource = new FakeVisibility();
  visibilitySource.visibilityState = "visible";
  let requests = 0;

  const monitor = createWebSessionMonitor({
    eventTarget,
    visibilitySource,
    revalidateOnStart: false,
    fetchImpl: async () => {
      requests += 1;
      return jsonResponse({ user_id: "u1" });
    },
    onChange() {},
  });

  monitor.start();
  monitor.stop();
  eventTarget.dispatch("pageshow", { persisted: true });
  visibilitySource.dispatch("visibilitychange");
  await flush();
  assert.equal(requests, 0);
});
