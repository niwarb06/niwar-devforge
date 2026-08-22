# Web BFF Core

Reusable same-origin authentication transport for DevForge web products.

It is intentionally built on the standard Web `Request`/`Response` APIs so it can be used directly from Next.js Route Handlers without exposing backend bearer credentials to browser JavaScript.

## Security defaults

- Browser credentials are accepted only on same-origin state-changing routes.
- Login stores the opaque backend session in a `Secure`, `HttpOnly`, `SameSite=Lax`, host-only cookie.
- The default cookie name uses the `__Host-` prefix, so no `Domain` attribute is allowed and `Path=/` is mandatory.
- The backend session token is never returned by the BFF login response body.
- Credential, session, and profile responses are marked `Cache-Control: no-store`.
- Protected backend calls are made server-side with the cookie value translated to `Authorization: Bearer ...`.
- Stale sessions clear the browser cookie.
- Logout revokes the backend session before clearing the browser cookie when the backend is reachable.
- JSON request bodies are content-type checked and size bounded.
- Unexpected upstream 5xx/non-JSON responses are converted to generic BFF errors rather than blindly relayed.

## Next.js Route Handler example

Create a server-only module once:

```ts
import { createWebAuthBff } from "@niwar-devforge/web-bff-core";

export const authBff = createWebAuthBff({
  backendApiBaseUrl: process.env.DEVFORGE_BACKEND_API_URL!,
  publicOrigin: process.env.DEVFORGE_PUBLIC_ORIGIN!,
});
```

Then wire thin same-origin Route Handlers, for example:

```ts
import { authBff } from "@/server/auth-bff";

export async function POST(request: Request): Promise<Response> {
  return authBff.login(request);
}
```

Recommended mappings:

- `POST /api/auth/register` -> `authBff.register`
- `POST /api/auth/session` -> `authBff.login`
- `DELETE /api/auth/session` -> `authBff.logout`
- `GET /api/auth/me` -> `authBff.me`
- `PATCH /api/auth/me` -> `authBff.updateProfile`

Do not import the configured BFF instance into Client Components. Keep backend URLs, cookie handling, and credential translation on the server boundary.

## Development cookies

The secure default cookie is correct for HTTPS environments. For plain HTTP localhost development, choose a non-`__Host-` cookie name and explicitly set `secureCookie: false`. Never carry that setting into staging or production.

## Current production blocker

The backend credential limiter currently keys direct client address at the backend boundary. When credentials arrive through a BFF/reverse-proxy hop, production deployment still needs an approved trusted-proxy/client-address policy so many browser users are not collapsed into one proxy address bucket. Do not solve this by blindly disabling or massively increasing abuse limits.

Until that deployment contract, browser-history revalidation integration, and production-like pilot evidence are complete, this package remains EXPERIMENTAL.
