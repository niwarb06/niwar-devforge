#!/usr/bin/env python3
"""Validate the Niwar DevForge chat/realtime contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("chat-contract.json")
EXPECTED_DOMAIN = "chat"
EXPECTED_CAPABILITIES = ["realtime_events"]


class ContractError(ValueError):
    """Raised when the chat contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("chat contract must be a JSON object")
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")

    if payload.get("domain") != EXPECTED_DOMAIN:
        raise ContractError(f"domain must be {EXPECTED_DOMAIN!r}")

    capabilities = payload.get("capabilities")
    if capabilities != EXPECTED_CAPABILITIES:
        raise ContractError(
            f"capabilities must be exactly {EXPECTED_CAPABILITIES!r} in this foundation slice"
        )

    if payload.get("provider_adapter_required") is not True:
        raise ContractError("provider_adapter_required must be true")

    allowed_keys = {
        "schema_version",
        "domain",
        "capabilities",
        "provider_adapter_required",
    }
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        raise ContractError(f"unknown contract keys: {', '.join(unknown_keys)}")


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"chat contract invalid: {exc}", file=sys.stderr)
        return 1

    print("chat contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
