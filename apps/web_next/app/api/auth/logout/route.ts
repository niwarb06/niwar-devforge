import { pilotBff } from "../../../../lib/bff";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  return await pilotBff.logout(request);
}
