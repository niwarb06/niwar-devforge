#!/usr/bin/env python3
"""Validate the Niwar DevForge Delivery/Logistics Pack contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("delivery-logistics-pack-contract.json")
EXPECTED_PACK = "delivery-logistics"
EXPECTED_CAPABILITIES = [
    "orders",
    "driver_courier_state",
    "assignment",
    "route_location",
    "proof_of_delivery",
]


class ContractError(ValueError):
    """Raised when the Delivery/Logistics Pack contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("delivery logistics pack contract must be a JSON object")
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
        print(f"delivery logistics pack contract invalid: {exc}", file=sys.stderr)
        return 1
    print("delivery logistics pack contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
