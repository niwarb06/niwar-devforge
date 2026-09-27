#!/usr/bin/env python3
"""Validate the Niwar DevForge localization contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("locales.json")
REQUIRED_BASELINE = {"ku": "rtl", "ar": "rtl", "en": "ltr"}
LOCALE_CODE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
VALID_DIRECTIONS = {"ltr", "rtl"}


class ContractError(ValueError):
    """Raised when the localization contract is invalid."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractError("localization contract must be a JSON object")
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")

    default_locale = payload.get("default_locale")
    if not isinstance(default_locale, str) or not default_locale:
        raise ContractError("default_locale must be a non-empty string")

    supported = payload.get("supported_locales")
    if not isinstance(supported, list) or not supported:
        raise ContractError("supported_locales must be a non-empty list")

    directions: dict[str, str] = {}
    for index, entry in enumerate(supported):
        if not isinstance(entry, dict):
            raise ContractError(f"supported_locales[{index}] must be an object")

        code = entry.get("code")
        native_name = entry.get("native_name")
        direction = entry.get("direction")

        if not isinstance(code, str) or not LOCALE_CODE_RE.fullmatch(code):
            raise ContractError(f"invalid locale code at supported_locales[{index}]")
        if code in directions:
            raise ContractError(f"duplicate locale code: {code}")
        if not isinstance(native_name, str) or not native_name.strip():
            raise ContractError(f"native_name must be non-empty for {code}")
        if direction not in VALID_DIRECTIONS:
            raise ContractError(f"invalid direction for {code}: {direction!r}")

        directions[code] = direction

    if default_locale not in directions:
        raise ContractError("default_locale must be present in supported_locales")

    for code, expected_direction in REQUIRED_BASELINE.items():
        actual_direction = directions.get(code)
        if actual_direction is None:
            raise ContractError(f"required baseline locale missing: {code}")
        if actual_direction != expected_direction:
            raise ContractError(
                f"required direction for {code} is {expected_direction}, got {actual_direction}"
            )


def main() -> int:
    try:
        validate_contract(load_contract())
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"localization contract invalid: {exc}", file=sys.stderr)
        return 1

    print("localization contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
