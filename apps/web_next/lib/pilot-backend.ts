import { randomUUID } from "node:crypto";

export interface PilotProfileRecord {
  user_id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
}

interface PilotBackendState {
  sessions: Set<string>;
  disabled: boolean;
}

const PILOT_IDENTIFIER = "pilot@example.test";
const PILOT_PASSWORD = "devforge-pilot-password";
const PILOT_PROFILE: PilotProfileRecord = {
  user_id: "00000000-0000-4000-8000-000000000001",
  email: PILOT_IDENTIFIER,
  display_name: "DevForge Pilot",
  is_active: true,
};

const globalState = globalThis as typeof globalThis & {
  __devforgePilotBackendState?: PilotBackendState;
};

export function pilotBackendEnabled(): boolean {
  return (
    process.env.NODE_ENV !== "production" ||
    process.env.DEVFORGE_PILOT_INPROCESS_BACKEND === "1"
  );
}

function state(): PilotBackendState {
  globalState.__devforgePilotBackendState ??= {
    sessions: new Set<string>(),
    disabled: false,
  };
  return globalState.__devforgePilotBackendState;
}

export function issuePilotSession(identifier: string, password: string): string | null {
  const current = state();
  if (current.disabled || identifier !== PILOT_IDENTIFIER || password !== PILOT_PASSWORD) {
    return null;
  }
  const token = `pilot-session-${randomUUID()}`;
  current.sessions.add(token);
  return token;
}

export function pilotProfileForToken(token: string): PilotProfileRecord | null {
  const current = state();
  if (current.disabled || !current.sessions.has(token)) return null;
  return PILOT_PROFILE;
}

export function revokePilotSession(token: string): boolean {
  return state().sessions.delete(token);
}

export function revokeAllPilotSessions(): void {
  state().sessions.clear();
}

export function setPilotUserDisabled(disabled: boolean): void {
  state().disabled = disabled;
}

export function resetPilotBackend(): void {
  const current = state();
  current.sessions.clear();
  current.disabled = false;
}

export function bearerToken(request: Request): string | null {
  const authorization = request.headers.get("authorization") ?? "";
  if (!authorization.startsWith("Bearer ")) return null;
  const token = authorization.slice("Bearer ".length);
  return token.length >= 16 && token === token.trim() ? token : null;
}
