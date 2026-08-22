"use client";

import {
  createWebSessionMonitor,
  type WebSessionMonitor,
  type WebSessionSnapshot,
} from "@niwar-devforge/web-session-core";
import { FormEvent, useEffect, useRef, useState } from "react";

type PilotProfile = {
  user_id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
};

const initialSnapshot: WebSessionSnapshot<PilotProfile> = {
  status: "idle",
  profile: null,
  source: null,
  checkedAtMs: null,
  errorCode: null,
};

function decodeProfile(value: unknown): PilotProfile {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("invalid_profile");
  }
  const profile = value as Record<string, unknown>;
  if (
    typeof profile.user_id !== "string" ||
    typeof profile.email !== "string" ||
    (profile.display_name !== null && typeof profile.display_name !== "string") ||
    typeof profile.is_active !== "boolean"
  ) {
    throw new TypeError("invalid_profile");
  }
  return {
    user_id: profile.user_id,
    email: profile.email,
    display_name: profile.display_name as string | null,
    is_active: profile.is_active,
  };
}

export function PilotClient() {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [identifier, setIdentifier] = useState("pilot@example.test");
  const [password, setPassword] = useState("correct-horse-battery-staple");
  const [actionError, setActionError] = useState<string | null>(null);
  const monitorRef = useRef<WebSessionMonitor<PilotProfile> | null>(null);

  useEffect(() => {
    const monitor = createWebSessionMonitor<PilotProfile>({
      decodeProfile,
      onChange: setSnapshot,
    });
    monitorRef.current = monitor;
    monitor.start();
    return () => {
      monitor.stop();
      monitorRef.current = null;
    };
  }, []);

  const login = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActionError(null);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ identifier, password }),
      cache: "no-store",
      redirect: "error",
    });
    if (!response.ok) {
      setActionError("login_failed");
      return;
    }
    await monitorRef.current?.revalidate("auth-change");
  };

  const logout = async () => {
    setActionError(null);
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      cache: "no-store",
      redirect: "error",
    });
    if (!response.ok) {
      setActionError("logout_failed");
    }
    await monitorRef.current?.revalidate("auth-change");
  };

  const revalidate = async () => {
    setActionError(null);
    await monitorRef.current?.revalidate("manual");
  };

  const authenticated = snapshot.status === "authenticated" && snapshot.profile !== null;

  return (
    <div className="pilot-grid">
      <div className="status-panel" aria-live="polite">
        <div>
          <span>Status</span>
          <strong data-testid="session-status">{snapshot.status}</strong>
        </div>
        <div>
          <span>Source</span>
          <strong data-testid="session-source">{snapshot.source ?? "none"}</strong>
        </div>
      </div>

      {!authenticated ? (
        <form onSubmit={login} className="form-panel">
          <label>
            Email
            <input
              aria-label="Email"
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              aria-label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>
          <button type="submit">Sign in</button>
        </form>
      ) : null}

      {authenticated ? (
        <section data-testid="protected-content" className="protected-panel">
          <h2>Protected pilot content</h2>
          <p data-testid="profile-email">{snapshot.profile.email}</p>
          <div className="actions">
            <button type="button" onClick={logout}>
              Sign out
            </button>
            <button type="button" onClick={revalidate}>
              Revalidate session
            </button>
            <a href="/public">Public page</a>
          </div>
        </section>
      ) : null}

      {snapshot.status === "checking" ? (
        <p data-testid="protected-gate">Protected content is gated while session state is checked.</p>
      ) : null}

      {snapshot.status === "error" ? (
        <p data-testid="session-error">Session revalidation failed without assuming logout.</p>
      ) : null}

      {actionError ? <p data-testid="action-error">{actionError}</p> : null}
    </div>
  );
}
