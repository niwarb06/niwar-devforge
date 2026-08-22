# Trusted Proxy and Client Address Contract

Status: IMPLEMENTED AS EXPERIMENTAL FOUNDATION POLICY

## Objective

Preserve meaningful per-client credential abuse limits through approved reverse-proxy and web-BFF hops without allowing arbitrary callers to spoof `X-Forwarded-For`.

## Backend rule

The backend trusts forwarding metadata only when the immediate network peer belongs to an explicitly configured trusted proxy CIDR.

Configure:

```text
DEVFORGE_TRUSTED_PROXY_CIDRS=["10.20.0.0/24","2001:db8:20::/64"]
```

The default is an empty list, which means the backend ignores `X-Forwarded-For` and uses the direct peer address.

Catch-all trust ranges (`0.0.0.0/0` and `::/0`) are rejected because they would make forwarding metadata spoofable from every peer.

When a direct peer is trusted, the resolver parses the full `X-Forwarded-For` chain and walks it from right to left. Trusted proxy hops are skipped and the first untrusted hop becomes the client boundary. If the forwarding chain is malformed, the backend falls back to the direct peer rather than accepting the malformed value.

## Web BFF rule

`web-bff-core` never copies an inbound browser `X-Forwarded-For` header automatically.

Products that have trustworthy platform/server connection metadata may configure:

```ts
createWebAuthBff({
  backendApiBaseUrl: process.env.DEVFORGE_BACKEND_API_URL!,
  publicOrigin: process.env.DEVFORGE_PUBLIC_ORIGIN!,
  resolveTrustedClientAddress: async (request) => {
    // Return exactly one client IP from trusted server/platform metadata.
    // Do not blindly return request.headers.get("x-forwarded-for").
    return resolveFromTrustedIngress(request);
  },
});
```

The resolver may return one IPv4/IPv6 literal or `null`. Invalid/multi-value output fails closed before the backend credential request is sent.

## Approved deployment patterns

### Reverse proxy directly in front of backend

1. The ingress proxy must remove or overwrite client-supplied forwarding headers.
2. The proxy appends/sets a sanitized `X-Forwarded-For` chain.
3. Backend `DEVFORGE_TRUSTED_PROXY_CIDRS` contains only the actual ingress/proxy network ranges that can connect to the backend.
4. The backend must not be reachable through an untrusted path that can source traffic from those trusted ranges.

### Browser -> ingress -> Web BFF -> backend

1. The public ingress establishes the real client address using its platform-supported transport metadata and sanitizes spoofable forwarding headers.
2. The BFF obtains that value through a deployment-specific `resolveTrustedClientAddress` adapter.
3. The BFF emits one `X-Forwarded-For` client IP on credential requests.
4. The backend trusts only the BFF/proxy CIDR that directly connects to it.
5. Browser-supplied forwarding headers are never treated as authoritative by the reusable BFF package.

## Prohibited patterns

- trusting `X-Forwarded-For` from arbitrary internet peers
- configuring `0.0.0.0/0` or `::/0` as trusted proxies
- copying a browser-provided forwarding header directly into `resolveTrustedClientAddress`
- weakening credential rate limits to compensate for a missing client-address deployment contract
- trusting a hostname or mutable DNS name as a proxy identity; use controlled network CIDRs

## Verification before production

A product deployment must prove all of the following before this path is considered production-ready:

- an untrusted direct caller cannot spoof a forwarded client address
- the real ingress/BFF peer falls inside the configured trusted CIDR and no broader network is trusted
- two browser clients behind the same BFF produce distinct client rate-limit buckets when their real addresses differ
- malformed forwarded chains fall back safely rather than bypassing limits
- ingress configuration overwrites/removes client-supplied forwarding metadata
- deployment topology and CIDR ownership are documented

The reusable implementation closes the code-level trusted-proxy blocker, but each production deployment still needs topology-specific configuration and evidence.
