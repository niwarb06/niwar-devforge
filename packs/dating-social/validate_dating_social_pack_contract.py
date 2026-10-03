#!/usr/bin/env python3
"""Validate the Niwar DevForge Dating/Social Pack contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("dating-social-pack-contract.json")
EXPECTED_PACK = "dating-social"
EXPECTED_CAPABILITIES = [
    "profiles",
    "discovery",
    "swipe_action_model",
    "match_state",
    "chat",
    "privacy",
    "safety",
]


class ContractError(ValueError):
    """Raised when the Dating/Social Pack contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("dating social pack contract must be a JSON object")
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    if payload.get("pack") != EXPECTED_PACK:
        raise ContractError(f"pack must be {EXPECTED_PACK!r}")
    if payload.get("capabilities") != EXPECTED_CAPABILITIES:
        raise ContractError(
            f"capabilities must be exactly {EXPECTED_CAPABILITIES!r} in this foundation slice"
        )
    allowed_keys = {"schema_version", "pack", "capabilities"}
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        raise ContractError(f"unknown contract keys: {', '.join(unknown_keys)}")


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"dating social pack contract invalid: {exc}", file=sys.stderr)
        return 1
    print("dating social pack contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
