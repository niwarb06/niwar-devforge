import "server-only";

import { createWebAuthBff } from "@niwar-devforge/web-bff-core";

const backendApiBaseUrl = process.env.DEVFORGE_BACKEND_API_BASE_URL;
const publicOrigin = process.env.DEVFORGE_PUBLIC_ORIGIN;

if (!backendApiBaseUrl || !publicOrigin) {
  throw new Error("DEVFORGE_BACKEND_API_BASE_URL and DEVFORGE_PUBLIC_ORIGIN are required");
}

const allowInsecureLocalhost =
  process.env.DEVFORGE_PILOT_ALLOW_INSECURE_LOCALHOST === "1";

const publicUrl = new URL(publicOrigin);
const localHostnames = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);
if (allowInsecureLocalhost && !localHostnames.has(publicUrl.hostname)) {
  throw new Error("insecure pilot cookies are allowed only on localhost loopback origins");
}

export const authBff = createWebAuthBff({
  backendApiBaseUrl,
  publicOrigin,
  secureCookie: !allowInsecureLocalhost,
  cookieName: allowInsecureLocalhost
    ? "devforge_session_pilot"
    : "__Host-devforge_session",
});
