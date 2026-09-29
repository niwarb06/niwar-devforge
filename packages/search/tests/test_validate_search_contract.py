from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_search_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_search_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_search_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_search_contract)


class SearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_search_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_search_contract.validate_contract(self.contract)

    def test_domain_is_search(self) -> None:
        self.assertEqual(self.contract["domain"], "search")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(
            self.contract["capabilities"],
            ["search", "filters", "pagination"],
        )

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].remove("filters")
        with self.assertRaises(validate_search_contract.ContractError):
            validate_search_contract.validate_contract(payload)

    def test_reordered_capabilities_fail(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["filters", "search", "pagination"]
        with self.assertRaises(validate_search_contract.ContractError):
            validate_search_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("favorites")
        with self.assertRaises(validate_search_contract.ContractError):
            validate_search_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_search_contract.ContractError):
            validate_search_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
