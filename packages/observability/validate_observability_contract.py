#!/usr/bin/env python3
"""Validate the Niwar DevForge observability contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("observability-contract.json")
REQUIRED_CAPABILITIES = {"structured_logging", "request_correlation"}
ALLOWED_CAPABILITIES = REQUIRED_CAPABILITIES


class ContractError(ValueError):
    """Raised when the observability contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("observability contract must be a JSON object")
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    if payload.get("module") != "observability":
        raise ContractError("module must be observability")

    capabilities = payload.get("required_capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ContractError("required_capabilities must be a non-empty list")
    if not all(isinstance(item, str) and item for item in capabilities):
        raise ContractError("required_capabilities entries must be non-empty strings")
    if len(capabilities) != len(set(capabilities)):
        raise ContractError("required_capabilities must not contain duplicates")

    capability_set = set(capabilities)
    missing = REQUIRED_CAPABILITIES - capability_set
    if missing:
        raise ContractError(f"missing required capabilities: {sorted(missing)}")
    unknown = capability_set - ALLOWED_CAPABILITIES
    if unknown:
        raise ContractError(f"unknown V1 capabilities: {sorted(unknown)}")

    if payload.get("correlation_field") != "request_id":
        raise ContractError("correlation_field must be request_id")
    if payload.get("external_exporter_required") is not False:
        raise ContractError("external_exporter_required must be false in V1")


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"observability contract invalid: {exc}", file=sys.stderr)
        return 1

    print("observability contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
