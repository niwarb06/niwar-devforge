import pytest
from fastapi import Request
from pydantic import ValidationError

from devforge_core.client_address import resolve_client_address
from devforge_core.config import Settings


def _request(client_host: str, forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode("ascii")))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": (client_host, 12345),
            "server": ("api.example.test", 443),
        }
    )


def test_untrusted_direct_peer_cannot_spoof_forwarded_client_address() -> None:
    request = _request("203.0.113.9", "198.51.100.7")

    assert resolve_client_address(request, ["10.0.0.0/8"]) == "203.0.113.9"


def test_trusted_proxy_chain_returns_first_untrusted_hop_from_the_right() -> None:
    request = _request("10.0.0.10", "192.0.2.99, 198.51.100.7, 10.0.0.9")

    assert resolve_client_address(request, ["10.0.0.0/8"]) == "198.51.100.7"


def test_trusted_proxy_chain_resolves_original_client_when_only_proxies_follow_it() -> None:
    request = _request("10.0.0.10", "198.51.100.7, 10.0.0.8, 10.0.0.9")

    assert resolve_client_address(request, ["10.0.0.0/8"]) == "198.51.100.7"


def test_malformed_forwarded_chain_fails_closed_to_direct_peer() -> None:
    request = _request("10.0.0.10", "198.51.100.7, not-an-ip")

    assert resolve_client_address(request, ["10.0.0.0/8"]) == "10.0.0.10"


def test_settings_normalize_proxy_networks_and_reject_trust_everyone() -> None:
    settings = Settings(trusted_proxy_cidrs=["10.23.4.5/8", "10.0.0.0/8"])
    assert settings.trusted_proxy_cidrs == ["10.0.0.0/8"]

    with pytest.raises(ValidationError):
        Settings(trusted_proxy_cidrs=["0.0.0.0/0"])

    with pytest.raises(ValidationError):
        Settings(trusted_proxy_cidrs=["::/0"])
