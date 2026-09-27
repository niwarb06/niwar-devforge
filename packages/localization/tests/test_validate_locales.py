from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_locales.py"
SPEC = importlib.util.spec_from_file_location("validate_locales", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_locales = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_locales)


class LocalizationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_locales.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_locales.validate_contract(self.contract)

    def test_required_directions(self) -> None:
        directions = {
            entry["code"]: entry["direction"]
            for entry in self.contract["supported_locales"]
        }
        self.assertEqual(directions["ku"], "rtl")
        self.assertEqual(directions["ar"], "rtl")
        self.assertEqual(directions["en"], "ltr")

    def test_duplicate_locale_code_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["supported_locales"].append(
            copy.deepcopy(payload["supported_locales"][0])
        )
        with self.assertRaises(validate_locales.ContractError):
            validate_locales.validate_contract(payload)

    def test_missing_required_baseline_locale_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["supported_locales"] = [
            entry for entry in payload["supported_locales"] if entry["code"] != "ku"
        ]
        with self.assertRaises(validate_locales.ContractError):
            validate_locales.validate_contract(payload)

    def test_invalid_direction_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["supported_locales"][0]["direction"] = "auto"
        with self.assertRaises(validate_locales.ContractError):
            validate_locales.validate_contract(payload)

    def test_default_locale_must_be_supported(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["default_locale"] = "fr"
        with self.assertRaises(validate_locales.ContractError):
            validate_locales.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
