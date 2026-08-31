import { createWebAuthBff } from "@niwar-devforge/web-bff-core";

const configuredPublicOrigin = process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN;
const configuredBackendApiBaseUrl = process.env.DEVFORGE_PILOT_BACKEND_API_BASE_URL;

if (
  process.env.NODE_ENV === "production" &&
  (!configuredPublicOrigin || !configuredBackendApiBaseUrl)
) {
  throw new Error(
    "production pilot requires explicit DEVFORGE_PILOT_PUBLIC_ORIGIN and DEVFORGE_PILOT_BACKEND_API_BASE_URL",
  );
}

const publicOrigin = configuredPublicOrigin ?? "http://127.0.0.1:3000";
const backendApiBaseUrl =
  configuredBackendApiBaseUrl ?? `${publicOrigin}/api/pilot-backend/v1`;

export const pilotBff = createWebAuthBff({
  publicOrigin,
  backendApiBaseUrl,
  cookieName: "devforge_pilot_session",
  secureCookie: publicOrigin.startsWith("https://"),
});
