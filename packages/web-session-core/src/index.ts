export type WebSessionStatus =
  | "idle"
  | "checking"
  | "authenticated"
  | "anonymous"
  | "error";

export type WebSessionSource =
  | "start"
  | "pageshow"
  | "bfcache"
  | "visible"
  | "manual"
  | "auth-change";

export interface WebSessionSnapshot<TProfile> {
  readonly status: WebSessionStatus;
  readonly profile: TProfile | null;
  readonly source: WebSessionSource | null;
  readonly checkedAtMs: number | null;
  readonly errorCode: "session_revalidation_failed" | null;
}

export interface BrowserEventLike {
  readonly type?: string;
  readonly persisted?: boolean;
}

export interface BrowserEventTargetLike {
  addEventListener(type: string, listener: (event: BrowserEventLike) => void): void;
  removeEventListener(type: string, listener: (event: BrowserEventLike) => void): void;
}

export interface VisibilitySourceLike extends BrowserEventTargetLike {
  readonly visibilityState: string;
}

export interface WebSessionMonitorConfig<TProfile> {
  readonly endpoint?: string;
  readonly fetchImpl?: typeof fetch;
  readonly eventTarget?: BrowserEventTargetLike;
  readonly visibilitySource?: VisibilitySourceLike;
  readonly maxResponseBytes?: number;
  readonly revalidateOnStart?: boolean;
  readonly now?: () => number;
  readonly decodeProfile?: (value: unknown) => TProfile;
  readonly onChange: (snapshot: WebSessionSnapshot<TProfile>) => void;
}

export interface WebSessionMonitor<TProfile> {
  start(): void;
  stop(): void;
  current(): WebSessionSnapshot<TProfile>;
  revalidate(source?: "manual" | "auth-change"): Promise<WebSessionSnapshot<TProfile>>;
}

const DEFAULT_ENDPOINT = "/api/auth/me";
const DEFAULT_MAX_RESPONSE_BYTES = 64 * 1024;
const MIN_RESPONSE_BYTES = 1024;
const MAX_RESPONSE_BYTES = 256 * 1024;

function initialSnapshot<TProfile>(): WebSessionSnapshot<TProfile> {
  return {
    status: "idle",
    profile: null,
    source: null,
    checkedAtMs: null,
    errorCode: null,
  };
}

function assertRelativeSessionEndpoint(endpoint: string): string {
  if (
    !endpoint.startsWith("/") ||
    endpoint.startsWith("//") ||
    endpoint.includes("\\") ||
    endpoint.includes("?") ||
    endpoint.includes("#") ||
    endpoint.includes("\r") ||
    endpoint.includes("\n")
  ) {
    throw new TypeError(
      "web session endpoint must be a root-relative same-origin path without query or fragment",
    );
  }
  return endpoint;
}

function normalizeMaxResponseBytes(value: number | undefined): number {
  const normalized = value ?? DEFAULT_MAX_RESPONSE_BYTES;
  if (
    !Number.isSafeInteger(normalized) ||
    normalized < MIN_RESPONSE_BYTES ||
    normalized > MAX_RESPONSE_BYTES
  ) {
    throw new TypeError(
      `maxResponseBytes must be an integer between ${MIN_RESPONSE_BYTES} and ${MAX_RESPONSE_BYTES}`,
    );
  }
  return normalized;
}

function defaultDecodeProfile<TProfile>(value: unknown): TProfile {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("session profile response must be a JSON object");
  }
  return value as TProfile;
}

async function readBoundedJson(response: Response, maxBytes: number): Promise<unknown> {
  const declaredLength = response.headers.get("content-length");
  if (declaredLength !== null) {
    const parsedLength = Number(declaredLength);
    if (Number.isFinite(parsedLength) && parsedLength > maxBytes) {
      throw new TypeError("session response exceeded configured size limit");
    }
  }

  const bytes = await response.arrayBuffer();
  if (bytes.byteLength > maxBytes) {
    throw new TypeError("session response exceeded configured size limit");
  }

  const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  return JSON.parse(text) as unknown;
}

function getDefaultEventTarget(): BrowserEventTargetLike | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window;
}

function getDefaultVisibilitySource(): VisibilitySourceLike | undefined {
  if (typeof document === "undefined") {
    return undefined;
  }
  return document;
}

export function createWebSessionMonitor<TProfile = Record<string, unknown>>(
  config: WebSessionMonitorConfig<TProfile>,
): WebSessionMonitor<TProfile> {
  const endpoint = assertRelativeSessionEndpoint(config.endpoint ?? DEFAULT_ENDPOINT);
  const maxResponseBytes = normalizeMaxResponseBytes(config.maxResponseBytes);
  const fetchImpl = config.fetchImpl ?? globalThis.fetch;
  if (typeof fetchImpl !== "function") {
    throw new TypeError("fetch implementation is required");
  }

  const eventTarget = config.eventTarget ?? getDefaultEventTarget();
  const visibilitySource = config.visibilitySource ?? getDefaultVisibilitySource();
  const now = config.now ?? Date.now;
  const decodeProfile = config.decodeProfile ?? defaultDecodeProfile<TProfile>;
  const revalidateOnStart = config.revalidateOnStart ?? true;

  let snapshot = initialSnapshot<TProfile>();
  let started = false;
  let requestGeneration = 0;
  let activeController: AbortController | null = null;
  let scheduled = false;
  let scheduledSource: WebSessionSource | null = null;

  const emit = (next: WebSessionSnapshot<TProfile>): WebSessionSnapshot<TProfile> => {
    snapshot = next;
    config.onChange(next);
    return next;
  };

  const schedule = (source: WebSessionSource): void => {
    scheduledSource = source === "bfcache" ? "bfcache" : (scheduledSource ?? source);
    if (scheduled) {
      return;
    }
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      const sourceToRun = scheduledSource ?? "manual";
      scheduledSource = null;
      if (started) {
        void performRevalidation(sourceToRun);
      }
    });
  };

  const performRevalidation = async (
    source: WebSessionSource,
  ): Promise<WebSessionSnapshot<TProfile>> => {
    requestGeneration += 1;
    const generation = requestGeneration;
    activeController?.abort();
    const controller = new AbortController();
    activeController = controller;

    emit({
      status: "checking",
      profile: null,
      source,
      checkedAtMs: null,
      errorCode: null,
    });

    try {
      const response = await fetchImpl(endpoint, {
        method: "GET",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        headers: {
          accept: "application/json",
        },
        signal: controller.signal,
      });

      if (generation !== requestGeneration) {
        return snapshot;
      }

      if (response.status === 401) {
        return emit({
          status: "anonymous",
          profile: null,
          source,
          checkedAtMs: now(),
          errorCode: null,
        });
      }

      if (!response.ok) {
        return emit({
          status: "error",
          profile: null,
          source,
          checkedAtMs: now(),
          errorCode: "session_revalidation_failed",
        });
      }

      const value = await readBoundedJson(response, maxResponseBytes);
      if (generation !== requestGeneration) {
        return snapshot;
      }
      const profile = decodeProfile(value);
      return emit({
        status: "authenticated",
        profile,
        source,
        checkedAtMs: now(),
        errorCode: null,
      });
    } catch (error: unknown) {
      if (generation !== requestGeneration || controller.signal.aborted) {
        return snapshot;
      }
      return emit({
        status: "error",
        profile: null,
        source,
        checkedAtMs: now(),
        errorCode: "session_revalidation_failed",
      });
    } finally {
      if (activeController === controller) {
        activeController = null;
      }
    }
  };

  const onPageShow = (event: BrowserEventLike): void => {
    schedule(event.persisted === true ? "bfcache" : "pageshow");
  };

  const onVisibilityChange = (): void => {
    if (visibilitySource?.visibilityState === "visible") {
      schedule("visible");
    }
  };

  return {
    start(): void {
      if (started) {
        return;
      }
      started = true;
      eventTarget?.addEventListener("pageshow", onPageShow);
      visibilitySource?.addEventListener("visibilitychange", onVisibilityChange);
      if (revalidateOnStart) {
        schedule("start");
      }
    },

    stop(): void {
      if (!started) {
        return;
      }
      started = false;
      eventTarget?.removeEventListener("pageshow", onPageShow);
      visibilitySource?.removeEventListener("visibilitychange", onVisibilityChange);
      requestGeneration += 1;
      activeController?.abort();
      activeController = null;
      scheduledSource = null;
    },

    current(): WebSessionSnapshot<TProfile> {
      return snapshot;
    },

    revalidate(
      source: "manual" | "auth-change" = "manual",
    ): Promise<WebSessionSnapshot<TProfile>> {
      return performRevalidation(source);
    },
  };
}
