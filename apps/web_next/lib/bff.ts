import { createWebAuthBff } from "@niwar-devforge/web-bff-core";

const publicOrigin = process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN ?? "http://127.0.0.1:3000";
const backendApiBaseUrl =
  process.env.DEVFORGE_PILOT_BACKEND_API_BASE_URL ?? `${publicOrigin}/api/pilot-backend/v1`;

export const pilotBff = createWebAuthBff({
  publicOrigin,
  backendApiBaseUrl,
  cookieName: "devforge_pilot_session",
  secureCookie: publicOrigin.startsWith("https://"),
});
