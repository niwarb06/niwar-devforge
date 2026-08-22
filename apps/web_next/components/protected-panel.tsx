"use client";

import { usePilotSession } from "./session-provider";

export function ProtectedPanel() {
  const { snapshot, logout } = usePilotSession();

  return (
    <main>
      <section>
        <h1>Protected pilot page</h1>
        <div className="status" data-testid="session-status">
          {snapshot.status}
        </div>
        <div className="status" data-testid="session-source">
          {snapshot.source ?? "none"}
        </div>

        {snapshot.status === "authenticated" && snapshot.profile ? (
          <div className="card" data-devforge-protected data-testid="protected-secret">
            Private pilot content for {snapshot.profile.email}
          </div>
        ) : null}

        {snapshot.status === "idle" || snapshot.status === "checking" ? (
          <p data-testid="protected-gate">Checking session before showing protected content…</p>
        ) : null}
        {snapshot.status === "anonymous" ? (
          <p data-testid="protected-anonymous">Sign in is required.</p>
        ) : null}
        {snapshot.status === "error" ? (
          <p data-testid="protected-error">Session validation is temporarily unavailable.</p>
        ) : null}

        <nav>
          <a href="/public">Leave protected page</a>
          <a href="/">Home</a>
        </nav>

        {snapshot.status === "authenticated" ? (
          <button data-testid="protected-logout" type="button" onClick={() => void logout()}>
            Sign out
          </button>
        ) : null}
      </section>
    </main>
  );
}
