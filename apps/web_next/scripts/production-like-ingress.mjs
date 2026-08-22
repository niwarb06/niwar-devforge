import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { request as httpRequest } from "node:http";
import { createServer } from "node:https";
import { join } from "node:path";
import { tmpdir } from "node:os";

const listenHost = process.env.DEVFORGE_INGRESS_HOST ?? "127.0.0.1";
const listenPort = Number.parseInt(process.env.DEVFORGE_INGRESS_PORT ?? "3443", 10);
const upstreamHost = process.env.DEVFORGE_INGRESS_UPSTREAM_HOST ?? "127.0.0.1";
const upstreamPort = Number.parseInt(process.env.DEVFORGE_INGRESS_UPSTREAM_PORT ?? "3000", 10);

if (!Number.isInteger(listenPort) || listenPort < 1 || listenPort > 65535) {
  throw new Error("DEVFORGE_INGRESS_PORT must be a valid TCP port");
}
if (!Number.isInteger(upstreamPort) || upstreamPort < 1 || upstreamPort > 65535) {
  throw new Error("DEVFORGE_INGRESS_UPSTREAM_PORT must be a valid TCP port");
}

const tlsDirectory = join(tmpdir(), `devforge-ingress-${process.pid}`);
const keyPath = join(tlsDirectory, "key.pem");
const certificatePath = join(tlsDirectory, "cert.pem");
mkdirSync(tlsDirectory, { recursive: true });

const openssl = spawnSync(
  "openssl",
  [
    "req",
    "-x509",
    "-newkey",
    "rsa:2048",
    "-sha256",
    "-nodes",
    "-days",
    "1",
    "-subj",
    "/CN=127.0.0.1",
    "-addext",
    "subjectAltName=IP:127.0.0.1",
    "-keyout",
    keyPath,
    "-out",
    certificatePath,
  ],
  { stdio: "inherit" },
);
if (openssl.status !== 0) {
  rmSync(tlsDirectory, { recursive: true, force: true });
  throw new Error("failed to generate ephemeral TLS certificate with openssl");
}

const blockedForwardingHeaders = new Set([
  "forwarded",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-proto",
  "x-real-ip",
  "x-devforge-ingress-client-ip",
]);

function normalizedPeerAddress(socketAddress) {
  if (!socketAddress) return null;
  if (socketAddress.startsWith("::ffff:")) return socketAddress.slice("::ffff:".length);
  if (socketAddress === "::1") return "127.0.0.1";
  return socketAddress;
}

const server = createServer(
  {
    key: readFileSync(keyPath),
    cert: readFileSync(certificatePath),
    minVersion: "TLSv1.2",
  },
  (request, response) => {
    if (request.url === "/_devforge_ingress_health") {
      response.writeHead(204, { "Cache-Control": "no-store" });
      response.end();
      return;
    }

    const clientAddress = normalizedPeerAddress(request.socket.remoteAddress);
    if (!clientAddress) {
      response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("client address unavailable");
      return;
    }

    const headers = {};
    for (const [name, value] of Object.entries(request.headers)) {
      const normalizedName = name.toLowerCase();
      if (blockedForwardingHeaders.has(normalizedName)) continue;
      if (normalizedName === "connection" || normalizedName === "proxy-connection") continue;
      if (value !== undefined) headers[name] = value;
    }

    headers["x-forwarded-for"] = clientAddress;
    headers["x-real-ip"] = clientAddress;
    headers["x-forwarded-proto"] = "https";
    headers["x-forwarded-host"] = request.headers.host ?? `${listenHost}:${listenPort}`;
    headers["x-devforge-ingress-client-ip"] = clientAddress;

    const upstream = httpRequest(
      {
        host: upstreamHost,
        port: upstreamPort,
        method: request.method,
        path: request.url,
        headers,
      },
      (upstreamResponse) => {
        response.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
        upstreamResponse.pipe(response);
      },
    );

    upstream.on("error", () => {
      if (!response.headersSent) {
        response.writeHead(502, { "Content-Type": "text/plain; charset=utf-8" });
      }
      response.end("upstream unavailable");
    });

    request.pipe(upstream);
  },
);

function shutdown(signal) {
  server.close(() => {
    rmSync(tlsDirectory, { recursive: true, force: true });
    process.exit(signal ? 0 : 1);
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("exit", () => rmSync(tlsDirectory, { recursive: true, force: true }));

server.listen(listenPort, listenHost, () => {
  console.log(`DevForge production-like ingress listening on https://${listenHost}:${listenPort}`);
});
