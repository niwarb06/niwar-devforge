import http from "node:http";

const host = "127.0.0.1";
const port = 4101;
const sessions = new Set();
let userEnabled = true;
let meDelayMs = 0;
let failMe = false;
let tokenCounter = 0;

const profile = {
  user_id: "11111111-1111-4111-8111-111111111111",
  email: "pilot@example.test",
  display_name: "Pilot User",
  is_active: true,
};

function sendJson(response, status, body, extraHeaders = {}) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    ...extraHeaders,
  });
  response.end(JSON.stringify(body));
}

function sendEmpty(response, status) {
  response.writeHead(status, { "cache-control": "no-store" });
  response.end();
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function bearerToken(request) {
  const authorization = request.headers.authorization;
  if (typeof authorization !== "string" || !authorization.startsWith("Bearer ")) {
    return null;
  }
  return authorization.slice("Bearer ".length);
}

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${host}:${port}`);

    if (request.method === "GET" && url.pathname === "/__test__/health") {
      sendJson(response, 200, { ok: true });
      return;
    }

    if (request.method === "POST" && url.pathname === "/__test__/reset") {
      sessions.clear();
      userEnabled = true;
      meDelayMs = 0;
      failMe = false;
      tokenCounter = 0;
      sendJson(response, 200, { ok: true });
      return;
    }

    if (request.method === "POST" && url.pathname === "/__test__/disable-user") {
      userEnabled = false;
      sendJson(response, 200, { ok: true });
      return;
    }

    if (request.method === "POST" && url.pathname === "/__test__/enable-user") {
      userEnabled = true;
      sendJson(response, 200, { ok: true });
      return;
    }

    if (request.method === "POST" && url.pathname === "/__test__/set-me-delay") {
      const body = await readJson(request);
      const candidate = Number(body.ms ?? 0);
      meDelayMs = Number.isFinite(candidate) && candidate >= 0 ? Math.min(candidate, 5000) : 0;
      sendJson(response, 200, { ok: true, meDelayMs });
      return;
    }

    if (request.method === "POST" && url.pathname === "/__test__/set-me-failure") {
      const body = await readJson(request);
      failMe = body.enabled === true;
      sendJson(response, 200, { ok: true, failMe });
      return;
    }

    if (request.method === "POST" && url.pathname === "/api/v1/auth/session") {
      const body = await readJson(request);
      if (
        body.identifier !== "pilot@example.test" ||
        body.password !== "correct-horse-battery-staple"
      ) {
        sendJson(response, 401, { code: "invalid_credentials", message: null });
        return;
      }
      tokenCounter += 1;
      const token = `pilot_session_${String(tokenCounter).padStart(24, "0")}`;
      sessions.add(token);
      sendJson(response, 200, {
        session_token: token,
        token_type: "bearer",
        expires_in_seconds: 3600,
      });
      return;
    }

    if (request.method === "DELETE" && url.pathname === "/api/v1/auth/session") {
      const token = bearerToken(request);
      if (token) sessions.delete(token);
      sendEmpty(response, 204);
      return;
    }

    if (request.method === "GET" && url.pathname === "/api/v1/users/me") {
      if (meDelayMs > 0) {
        await new Promise((resolve) => setTimeout(resolve, meDelayMs));
      }
      if (failMe) {
        sendJson(response, 503, { code: "temporarily_unavailable", message: null });
        return;
      }
      const token = bearerToken(request);
      if (!token || !sessions.has(token) || !userEnabled) {
        sendJson(response, 401, { code: "not_authenticated", message: null });
        return;
      }
      sendJson(response, 200, { ...profile, is_active: userEnabled });
      return;
    }

    sendJson(response, 404, { code: "not_found", message: null });
  } catch {
    sendJson(response, 500, { code: "test_backend_error", message: null });
  }
});

server.listen(port, host, () => {
  console.log(`DevForge browser-pilot backend listening on http://${host}:${port}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
