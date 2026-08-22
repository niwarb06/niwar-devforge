export type TrustedClientAddressResolver = (
  request: Request,
) => string | null | Promise<string | null>;

export interface WebBffConfig {
  backendApiBaseUrl: string;
  publicOrigin: string;
  cookieName?: string;
  secureCookie?: boolean;
  maxRequestBodyBytes?: number;
  resolveTrustedClientAddress?: TrustedClientAddressResolver;
  fetchImpl?: typeof fetch;
}

export interface WebAuthBffHandlers {
  register(request: Request): Promise<Response>;
  login(request: Request): Promise<Response>;
  logout(request: Request): Promise<Response>;
  me(request: Request): Promise<Response>;
  updateProfile(request: Request): Promise<Response>;
}

interface NormalizedConfig {
  backendApiBaseUrl: string;
  publicOrigin: string;
  cookieName: string;
  secureCookie: boolean;
  maxRequestBodyBytes: number;
  resolveTrustedClientAddress: TrustedClientAddressResolver | undefined;
  fetchImpl: typeof fetch;
}

interface BackendSessionResponse {
  session_token: string;
  expires_in_seconds: number;
}

class BffRequestError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

const DEFAULT_COOKIE_NAME = "__Host-devforge_session";
const DEFAULT_MAX_REQUEST_BODY_BYTES = 16 * 1024;
const MAX_RELAY_BODY_BYTES = 64 * 1024;
const COOKIE_NAME_PATTERN = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

function normalizeConfig(config: WebBffConfig): NormalizedConfig {
  const backend = new URL(config.backendApiBaseUrl);
  if (backend.protocol !== "http:" && backend.protocol !== "https:") {
    throw new Error("backendApiBaseUrl must use http or https");
  }
  if (backend.username || backend.password || backend.search || backend.hash) {
    throw new Error("backendApiBaseUrl must not contain credentials, query, or fragment");
  }

  const publicUrl = new URL(config.publicOrigin);
  if (publicUrl.protocol !== "http:" && publicUrl.protocol !== "https:") {
    throw new Error("publicOrigin must use http or https");
  }
  if (
    publicUrl.pathname !== "/" ||
    publicUrl.search ||
    publicUrl.hash ||
    publicUrl.username ||
    publicUrl.password
  ) {
    throw new Error("publicOrigin must be an origin without path, credentials, query, or fragment");
  }

  const cookieName = config.cookieName ?? DEFAULT_COOKIE_NAME;
  if (!COOKIE_NAME_PATTERN.test(cookieName)) {
    throw new Error("cookieName contains invalid characters");
  }

  const secureCookie = config.secureCookie ?? true;
  if (cookieName.startsWith("__Host-") && !secureCookie) {
    throw new Error("__Host- cookies require secureCookie=true");
  }

  const maxRequestBodyBytes = config.maxRequestBodyBytes ?? DEFAULT_MAX_REQUEST_BODY_BYTES;
  if (
    !Number.isSafeInteger(maxRequestBodyBytes) ||
    maxRequestBodyBytes < 1024 ||
    maxRequestBodyBytes > 1_048_576
  ) {
    throw new Error("maxRequestBodyBytes must be an integer between 1024 and 1048576");
  }

  return {
    backendApiBaseUrl: backend.toString().replace(/\/+$/, "") + "/",
    publicOrigin: publicUrl.origin,
    cookieName,
    secureCookie,
    maxRequestBodyBytes,
    resolveTrustedClientAddress: config.resolveTrustedClientAddress,
    fetchImpl: config.fetchImpl ?? globalThis.fetch,
  };
}

function endpoint(config: NormalizedConfig, path: string): string {
  return new URL(path.replace(/^\/+/, ""), config.backendApiBaseUrl).toString();
}

function noStoreHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  headers.set("Cache-Control", "no-store");
  headers.set("Pragma", "no-cache");
  return headers;
}

function jsonResponse(status: number, body: unknown, extra?: HeadersInit): Response {
  const headers = noStoreHeaders(extra);
  headers.set("Content-Type", "application/json; charset=utf-8");
  return new Response(JSON.stringify(body), { status, headers });
}

function publicError(status: number, code: string, extra?: HeadersInit): Response {
  return jsonResponse(status, { code, message: null }, extra);
}

function assertSameOrigin(request: Request, config: NormalizedConfig): void {
  const origin = request.headers.get("origin");
  if (!origin) {
    throw new BffRequestError(403, "same_origin_required");
  }

  let normalizedOrigin: string;
  try {
    normalizedOrigin = new URL(origin).origin;
  } catch {
    throw new BffRequestError(403, "same_origin_required");
  }

  if (normalizedOrigin !== config.publicOrigin) {
    throw new BffRequestError(403, "same_origin_required");
  }

  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite.toLowerCase() !== "same-origin") {
    throw new BffRequestError(403, "same_origin_required");
  }
}

async function readJsonBody(request: Request, config: NormalizedConfig): Promise<string> {
  const contentType = request.headers.get("content-type")?.toLowerCase() ?? "";
  if (!contentType.startsWith("application/json")) {
    throw new BffRequestError(415, "json_required");
  }

  const declaredLength = request.headers.get("content-length");
  if (declaredLength) {
    const parsed = Number.parseInt(declaredLength, 10);
    if (Number.isFinite(parsed) && parsed > config.maxRequestBodyBytes) {
      throw new BffRequestError(413, "request_too_large");
    }
  }

  const body = await request.text();
  if (new TextEncoder().encode(body).byteLength > config.maxRequestBodyBytes) {
    throw new BffRequestError(413, "request_too_large");
  }
  return body;
}

function cookieValue(request: Request, name: string): string | null {
  const header = request.headers.get("cookie");
  if (!header) return null;

  for (const part of header.split(";")) {
    const trimmed = part.trim();
    const separator = trimmed.indexOf("=");
    if (separator <= 0) continue;
    if (trimmed.slice(0, separator) !== name) continue;
    try {
      return decodeURIComponent(trimmed.slice(separator + 1));
    } catch {
      return null;
    }
  }
  return null;
}

function sessionCookie(config: NormalizedConfig, token: string, maxAgeSeconds: number): string {
  const attributes = [
    `${config.cookieName}=${encodeURIComponent(token)}`,
    "Path=/",
    `Max-Age=${Math.max(1, Math.trunc(maxAgeSeconds))}`,
    "HttpOnly",
    "SameSite=Lax",
  ];
  if (config.secureCookie) attributes.push("Secure");
  return attributes.join("; ");
}

function clearSessionCookie(config: NormalizedConfig): string {
  const attributes = [
    `${config.cookieName}=`,
    "Path=/",
    "Max-Age=0",
    "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
    "HttpOnly",
    "SameSite=Lax",
  ];
  if (config.secureCookie) attributes.push("Secure");
  return attributes.join("; ");
}

function withClearedCookie(response: Response, config: NormalizedConfig): Response {
  if (response.status === 403) return response;
  response.headers.append("Set-Cookie", clearSessionCookie(config));
  return response;
}

async function safeRelay(upstream: Response): Promise<Response> {
  const body = await upstream.text();
  const bodyBytes = new TextEncoder().encode(body).byteLength;
  const contentType = upstream.headers.get("content-type")?.toLowerCase() ?? "";

  if (upstream.status >= 500) {
    if (
      upstream.status === 503 &&
      contentType.includes("application/json") &&
      bodyBytes <= MAX_RELAY_BODY_BYTES
    ) {
      try {
        const parsed = JSON.parse(body) as { code?: unknown };
        if (parsed.code === "temporarily_unavailable") {
          return jsonResponse(503, parsed);
        }
      } catch {
        // Fall through to the generic upstream error below.
      }
    }
    return publicError(502, "upstream_unavailable");
  }

  if (bodyBytes > MAX_RELAY_BODY_BYTES || !contentType.includes("application/json")) {
    if (upstream.status === 204) {
      return new Response(null, { status: 204, headers: noStoreHeaders() });
    }
    return publicError(502, "invalid_upstream_response");
  }

  const headers = noStoreHeaders({ "Content-Type": "application/json; charset=utf-8" });
  const retryAfter = upstream.headers.get("retry-after");
  if (retryAfter) headers.set("Retry-After", retryAfter);
  return new Response(body, { status: upstream.status, headers });
}

async function backendFetch(
  config: NormalizedConfig,
  path: string,
  init: RequestInit,
): Promise<Response> {
  try {
    return await config.fetchImpl(endpoint(config, path), {
      ...init,
      cache: "no-store",
      redirect: "error",
    });
  } catch {
    throw new BffRequestError(502, "upstream_unavailable");
  }
}

function authorizationHeaders(token: string, extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  headers.set("Authorization", `Bearer ${token}`);
  return headers;
}

function isValidIpLiteral(value: string): boolean {
  if (!value || value.length > 64 || value !== value.trim() || /[\s,]/.test(value)) {
    return false;
  }

  if (value.includes(":")) {
    try {
      new URL(`http://[${value}]/`);
      return true;
    } catch {
      return false;
    }
  }

  const parts = value.split(".");
  if (parts.length !== 4) return false;
  return parts.every((part) => {
    if (!/^(0|[1-9][0-9]{0,2})$/.test(part)) return false;
    const octet = Number(part);
    return octet >= 0 && octet <= 255;
  });
}

async function credentialHeaders(request: Request, config: NormalizedConfig): Promise<Headers> {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (!config.resolveTrustedClientAddress) return headers;

  const clientAddress = await config.resolveTrustedClientAddress(request);
  if (clientAddress === null) return headers;
  if (!isValidIpLiteral(clientAddress)) {
    throw new Error("resolveTrustedClientAddress must return one valid IP literal or null");
  }

  headers.set("X-Forwarded-For", clientAddress);
  return headers;
}

function handleRequestError(error: unknown): Response {
  if (error instanceof BffRequestError) {
    return publicError(error.status, error.code);
  }
  return publicError(500, "bff_internal_error");
}

function parseSessionResponse(body: string): BackendSessionResponse | null {
  try {
    const parsed = JSON.parse(body) as Partial<BackendSessionResponse>;
    if (
      typeof parsed.session_token !== "string" ||
      parsed.session_token.length < 16 ||
      typeof parsed.expires_in_seconds !== "number" ||
      !Number.isSafeInteger(parsed.expires_in_seconds) ||
      parsed.expires_in_seconds <= 0
    ) {
      return null;
    }
    return {
      session_token: parsed.session_token,
      expires_in_seconds: parsed.expires_in_seconds,
    };
  } catch {
    return null;
  }
}

export function createWebAuthBff(input: WebBffConfig): WebAuthBffHandlers {
  const config = normalizeConfig(input);

  return {
    async register(request: Request): Promise<Response> {
      try {
        assertSameOrigin(request, config);
        const body = await readJsonBody(request, config);
        const upstream = await backendFetch(config, "auth/register", {
          method: "POST",
          headers: await credentialHeaders(request, config),
          body,
        });
        return await safeRelay(upstream);
      } catch (error) {
        return handleRequestError(error);
      }
    },

    async login(request: Request): Promise<Response> {
      try {
        assertSameOrigin(request, config);
        const body = await readJsonBody(request, config);
        const upstream = await backendFetch(config, "auth/session", {
          method: "POST",
          headers: await credentialHeaders(request, config),
          body,
        });

        if (!upstream.ok) return await safeRelay(upstream);
        const session = parseSessionResponse(await upstream.text());
        if (!session) return publicError(502, "invalid_upstream_response");

        const headers = noStoreHeaders({ "Content-Type": "application/json; charset=utf-8" });
        headers.append(
          "Set-Cookie",
          sessionCookie(config, session.session_token, session.expires_in_seconds),
        );
        return new Response(
          JSON.stringify({
            authenticated: true,
            expires_in_seconds: session.expires_in_seconds,
          }),
          { status: 200, headers },
        );
      } catch (error) {
        return handleRequestError(error);
      }
    },

    async logout(request: Request): Promise<Response> {
      try {
        assertSameOrigin(request, config);
        const token = cookieValue(request, config.cookieName);
        if (!token) {
          return withClearedCookie(
            new Response(null, { status: 204, headers: noStoreHeaders() }),
            config,
          );
        }

        const upstream = await backendFetch(config, "auth/session", {
          method: "DELETE",
          headers: authorizationHeaders(token),
        });

        if (upstream.status === 204 || upstream.status === 401) {
          return withClearedCookie(
            new Response(null, { status: 204, headers: noStoreHeaders() }),
            config,
          );
        }
        return withClearedCookie(await safeRelay(upstream), config);
      } catch (error) {
        return withClearedCookie(handleRequestError(error), config);
      }
    },

    async me(request: Request): Promise<Response> {
      const token = cookieValue(request, config.cookieName);
      if (!token) return publicError(401, "not_authenticated");

      try {
        const upstream = await backendFetch(config, "users/me", {
          method: "GET",
          headers: authorizationHeaders(token),
        });
        const response = await safeRelay(upstream);
        return upstream.status === 401 ? withClearedCookie(response, config) : response;
      } catch (error) {
        return handleRequestError(error);
      }
    },

    async updateProfile(request: Request): Promise<Response> {
      try {
        assertSameOrigin(request, config);
        const token = cookieValue(request, config.cookieName);
        if (!token) return publicError(401, "not_authenticated");
        const body = await readJsonBody(request, config);
        const upstream = await backendFetch(config, "users/me/profile", {
          method: "PATCH",
          headers: authorizationHeaders(token, { "Content-Type": "application/json" }),
          body,
        });
        const response = await safeRelay(upstream);
        return upstream.status === 401 ? withClearedCookie(response, config) : response;
      } catch (error) {
        return handleRequestError(error);
      }
    },
  };
}
