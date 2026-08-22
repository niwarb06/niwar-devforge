import { authBff } from "../../../../server/auth-bff";

export async function POST(request: Request) {
  return authBff.login(request);
}
