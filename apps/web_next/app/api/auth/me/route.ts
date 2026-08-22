import { pilotBff } from "../../../../lib/bff";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request): Promise<Response> {
  return await pilotBff.me(request);
}
