from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_reviews_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_reviews_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_reviews_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_reviews_contract)


class ReviewsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_reviews_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_reviews_contract.validate_contract(self.contract)

    def test_domain_is_reviews(self) -> None:
        self.assertEqual(self.contract["domain"], "reviews")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(
            self.contract["capabilities"],
            ["reviews", "ratings"],
        )

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].remove("ratings")
        with self.assertRaises(validate_reviews_contract.ContractError):
            validate_reviews_contract.validate_contract(payload)

    def test_reordered_capabilities_fail(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["ratings", "reviews"]
        with self.assertRaises(validate_reviews_contract.ContractError):
            validate_reviews_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("comments")
        with self.assertRaises(validate_reviews_contract.ContractError):
            validate_reviews_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_reviews_contract.ContractError):
            validate_reviews_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
