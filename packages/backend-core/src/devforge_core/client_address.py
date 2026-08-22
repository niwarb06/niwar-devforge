from collections.abc import Iterable
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)

from fastapi import Request

IpAddress = IPv4Address | IPv6Address
IpNetwork = IPv4Network | IPv6Network


def parse_trusted_proxy_networks(cidrs: Iterable[str]) -> tuple[IpNetwork, ...]:
    return tuple(ip_network(cidr, strict=False) for cidr in cidrs)


def _parse_ip(value: str) -> IpAddress | None:
    candidate = value.strip()
    if not candidate or len(candidate) > 64:
        return None
    try:
        return ip_address(candidate)
    except ValueError:
        return None


def _is_trusted(address: IpAddress, networks: tuple[IpNetwork, ...]) -> bool:
    return any(address in network for network in networks)


def resolve_client_address(request: Request, trusted_proxy_cidrs: Iterable[str]) -> str:
    """Resolve a rate-limit client address without trusting arbitrary forwarding headers.

    X-Forwarded-For is considered only when the immediate peer address belongs to an
    explicitly configured trusted proxy network. The chain is then walked from the
    nearest hop toward the original client, skipping trusted proxy hops. A malformed
    forwarding chain fails closed to the direct peer address instead of accepting a
    spoofable value.
    """

    direct_raw = "unknown" if request.client is None else request.client.host
    direct = _parse_ip(direct_raw)
    if direct is None:
        return direct_raw

    networks = parse_trusted_proxy_networks(trusted_proxy_cidrs)
    if not networks or not _is_trusted(direct, networks):
        return str(direct)

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return str(direct)

    forwarded_addresses: list[IpAddress] = []
    for item in forwarded.split(","):
        parsed = _parse_ip(item)
        if parsed is None:
            return str(direct)
        forwarded_addresses.append(parsed)

    if not forwarded_addresses:
        return str(direct)

    for candidate in reversed(forwarded_addresses):
        if _is_trusted(candidate, networks):
            continue
        return str(candidate)

    # Every forwarded hop is trusted. The left-most value is the farthest known hop
    # and is the best available client boundary after a trusted ingress sanitized it.
    return str(forwarded_addresses[0])
