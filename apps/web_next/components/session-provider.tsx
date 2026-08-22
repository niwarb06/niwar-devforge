"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  createWebSessionMonitor,
  type WebSessionMonitor,
  type WebSessionSnapshot,
} from "@niwar-devforge/web-session-core";

export interface PilotProfile {
  user_id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
}

interface SessionContextValue {
  snapshot: WebSessionSnapshot<PilotProfile>;
  login(identifier: string, password: string): Promise<boolean>;
  logout(): Promise<void>;
  revalidate(): Promise<WebSessionSnapshot<PilotProfile>>;
}

const INITIAL_SNAPSHOT: WebSessionSnapshot<PilotProfile> = {
  status: "idle",
  profile: null,
  source: null,
  checkedAtMs: null,
  errorCode: null,
};

const SessionContext = createContext<SessionContextValue | null>(null);

function decodeProfile(value: unknown): PilotProfile {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("invalid profile");
  }

  const profile = value as Record<string, unknown>;
  if (
    typeof profile.user_id !== "string" ||
    typeof profile.email !== "string" ||
    (profile.display_name !== null && typeof profile.display_name !== "string") ||
    typeof profile.is_active !== "boolean"
  ) {
    throw new TypeError("invalid profile");
  }

  return {
    user_id: profile.user_id,
    email: profile.email,
    display_name: profile.display_name,
    is_active: profile.is_active,
  };
}

function setProtectedDomTrusted(authenticated: boolean): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.devforgeSessionTrusted = authenticated ? "true" : "false";
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<WebSessionSnapshot<PilotProfile>>(INITIAL_SNAPSHOT);
  const monitorRef = useRef<WebSessionMonitor<PilotProfile> | null>(null);

  if (monitorRef.current === null && typeof window !== "undefined") {
    monitorRef.current = createWebSessionMonitor<PilotProfile>({
      decodeProfile,
      onChange(next) {
        setProtectedDomTrusted(next.status === "authenticated");
        setSnapshot(next);
      },
    });
  }

  useEffect(() => {
    setProtectedDomTrusted(false);
    const monitor = monitorRef.current;
    if (!monitor) return undefined;
    monitor.start();
    return () => {
      monitor.stop();
      setProtectedDomTrusted(false);
    };
  }, []);

  const revalidate = useCallback(async () => {
    const monitor = monitorRef.current;
    if (!monitor) return INITIAL_SNAPSHOT;
    return await monitor.revalidate("auth-change");
  }, []);

  const login = useCallback(async (identifier: string, password: string) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ identifier, password }),
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
    if (!response.ok) return false;
    const next = await revalidate();
    return next.status === "authenticated";
  }, [revalidate]);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error",
    });
    await revalidate();
  }, [revalidate]);

  const value = useMemo<SessionContextValue>(
    () => ({ snapshot, login, logout, revalidate }),
    [snapshot, login, logout, revalidate],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function usePilotSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("SessionProvider is required");
  return value;
}
