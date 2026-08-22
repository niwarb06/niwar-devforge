import {
  bearerToken,
  issuePilotSession,
  revokePilotSession,
} from "../../../../../../lib/pilot-backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const noStoreHeaders = { "cache-control": "no-store", pragma: "no-cache" };

export async function POST(request: Request): Promise<Response> {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return Response.json(
      { code: "invalid_request", message: null },
      { status: 400, headers: noStoreHeaders },
    );
  }

  const value = payload as { identifier?: unknown; password?: unknown };
  if (typeof value.identifier !== "string" || typeof value.password !== "string") {
    return Response.json(
      { code: "invalid_credentials", message: null },
      { status: 401, headers: noStoreHeaders },
    );
  }

  const token = issuePilotSession(value.identifier, value.password);
  if (!token) {
    return Response.json(
      { code: "invalid_credentials", message: null },
      { status: 401, headers: noStoreHeaders },
    );
  }

  return Response.json(
    {
      session_token: token,
      token_type: "bearer",
      expires_in_seconds: 3600,
    },
    { status: 200, headers: noStoreHeaders },
  );
}

export async function DELETE(request: Request): Promise<Response> {
  const token = bearerToken(request);
  if (!token || !revokePilotSession(token)) {
    return Response.json(
      { code: "not_authenticated", message: null },
      { status: 401, headers: noStoreHeaders },
    );
  }
  return new Response(null, { status: 204, headers: noStoreHeaders });
}
