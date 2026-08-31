import {
  pilotBackendEnabled,
  resetPilotBackend,
  revokeAllPilotSessions,
  setPilotUserDisabled,
} from "../../../lib/pilot-backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const noStoreHeaders = { "cache-control": "no-store", pragma: "no-cache" };

export async function POST(request: Request): Promise<Response> {
  if (
    !pilotBackendEnabled() ||
    process.env.DEVFORGE_PILOT_TEST_CONTROL !== "1" ||
    request.headers.get("x-devforge-pilot-control") !== "pilot-e2e"
  ) {
    return new Response(null, { status: 404, headers: noStoreHeaders });
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ ok: false }, { status: 400, headers: noStoreHeaders });
  }

  const action = (payload as { action?: unknown }).action;
  switch (action) {
    case "reset":
      resetPilotBackend();
      break;
    case "revoke":
      revokeAllPilotSessions();
      break;
    case "disable":
      setPilotUserDisabled(true);
      break;
    case "enable":
      setPilotUserDisabled(false);
      break;
    default:
      return Response.json({ ok: false }, { status: 400, headers: noStoreHeaders });
  }

  return Response.json({ ok: true }, { status: 200, headers: noStoreHeaders });
}
