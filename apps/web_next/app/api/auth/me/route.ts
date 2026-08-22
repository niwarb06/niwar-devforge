import { authBff } from "../../../../server/auth-bff";

export async function GET(request: Request) {
  return authBff.me(request);
}
