import { createWebAuthBff } from "@niwar-devforge/web-bff-core";

const configuredPublicOrigin = process.env.DEVFORGE_PILOT_PUBLIC_ORIGIN;
const configuredBackendApiBaseUrl = process.env.DEVFORGE_PILOT_BACKEND_API_BASE_URL;
const trustIngressClientAddress =
  process.env.DEVFORGE_PILOT_TRUST_INGRESS_CLIENT_IP === "1";

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

if (trustIngressClientAddress && !publicOrigin.startsWith("https://")) {
  throw new Error("trusted ingress client-address mode requires an https public origin");
}

export const pilotBff = createWebAuthBff({
  publicOrigin,
  backendApiBaseUrl,
  cookieName: "devforge_pilot_session",
  secureCookie: publicOrigin.startsWith("https://"),
  // Deployment-specific adapter. Enable only when the BFF is reachable solely through
  // an ingress that removes/overwrites this header from every external request.
  resolveTrustedClientAddress: trustIngressClientAddress
    ? async (request) => request.headers.get("x-devforge-ingress-client-ip")
    : undefined,
});
