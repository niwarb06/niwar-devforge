"use client";

import { type FormEvent, useState } from "react";

import { usePilotSession } from "./session-provider";

export function HomePanel() {
  const { snapshot, login, logout } = usePilotSession();
  const [identifier, setIdentifier] = useState("pilot@example.test");
  const [password, setPassword] = useState("devforge-pilot-password");
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      const ok = await login(identifier, password);
      setMessage(ok ? "Signed in" : "Sign-in failed");
    } catch {
      setMessage("Sign-in failed");
    }
  }

  return (
    <main>
      <section>
        <h1>DevForge Web Auth Pilot</h1>
        <p>
          Real Next.js browser proof for the server-only BFF cookie boundary and browser session
          revalidation lifecycle.
        </p>

        <div className="card">
          <div className="status" data-testid="session-status">
            {snapshot.status}
          </div>
          <div className="status" data-testid="session-source">
            {snapshot.source ?? "none"}
          </div>
          {snapshot.status === "authenticated" && snapshot.profile ? (
            <p data-testid="signed-in-email">{snapshot.profile.email}</p>
          ) : null}
        </div>

        {snapshot.status !== "authenticated" ? (
          <form onSubmit={submit}>
            <label>
              Email
              <input
                data-testid="identifier"
                autoComplete="username"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
              />
            </label>
            <label>
              Password
              <input
                data-testid="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <button data-testid="login" type="submit" disabled={snapshot.status === "checking"}>
              Sign in
            </button>
          </form>
        ) : (
          <button data-testid="logout" type="button" onClick={() => void logout()}>
            Sign out
          </button>
        )}

        {message ? <p data-testid="auth-message">{message}</p> : null}

        <nav>
          <a href="/protected">Protected page</a>
          <a href="/public">Public page</a>
        </nav>
      </section>
    </main>
  );
}
