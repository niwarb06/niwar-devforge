#!/usr/bin/env python3
"""Validate the Niwar DevForge storage capability contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("storage-contract.json")
REQUIRED_CAPABILITIES = {
    "file_upload",
    "private_access",
    "signed_access",
    "provider_adapter",
}
CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class ContractError(ValueError):
    """Raised when the storage contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("storage contract must be a JSON object")
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")

    if payload.get("module") != "storage":
        raise ContractError("module must be 'storage'")

    capabilities = payload.get("required_capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ContractError("required_capabilities must be a non-empty list")

    seen: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, str) or not CAPABILITY_RE.fullmatch(capability):
            raise ContractError(f"invalid capability at required_capabilities[{index}]")
        if capability in seen:
            raise ContractError(f"duplicate capability: {capability}")
        seen.add(capability)

    missing = sorted(REQUIRED_CAPABILITIES - seen)
    if missing:
        raise ContractError(f"missing required capabilities: {', '.join(missing)}")


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"storage contract invalid: {exc}", file=sys.stderr)
        return 1

    print("storage contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
