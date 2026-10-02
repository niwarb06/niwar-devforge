#!/usr/bin/env python3
"""Validate the Niwar DevForge wallet/ledger contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("wallet-ledger-contract.json")
EXPECTED_DOMAIN = "wallet_ledger"
EXPECTED_CAPABILITIES = ["wallet_ledger"]


class ContractError(ValueError):
    """Raised when the wallet/ledger contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("wallet/ledger contract must be a JSON object")
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

    allowed_keys = {"schema_version", "domain", "capabilities"}
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        raise ContractError(f"unknown contract keys: {', '.join(unknown_keys)}")


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"wallet/ledger contract invalid: {exc}", file=sys.stderr)
        return 1

    print("wallet/ledger contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
