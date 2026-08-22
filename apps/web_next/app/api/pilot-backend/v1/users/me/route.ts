import {
  bearerToken,
  pilotProfileForToken,
} from "../../../../../../lib/pilot-backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const noStoreHeaders = { "cache-control": "no-store", pragma: "no-cache" };

export async function GET(request: Request): Promise<Response> {
  const token = bearerToken(request);
  const profile = token ? pilotProfileForToken(token) : null;
  if (!profile) {
    return Response.json(
      { code: "not_authenticated", message: null },
      { status: 401, headers: noStoreHeaders },
    );
  }
  return Response.json(profile, { status: 200, headers: noStoreHeaders });
}
