from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_subscriptions_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_subscriptions_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_subscriptions_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_subscriptions_contract)


class SubscriptionsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_subscriptions_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_subscriptions_contract.validate_contract(self.contract)

    def test_domain_is_subscriptions(self) -> None:
        self.assertEqual(self.contract["domain"], "subscriptions")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(self.contract["capabilities"], ["subscriptions"])

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = []
        with self.assertRaises(validate_subscriptions_contract.ContractError):
            validate_subscriptions_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("coupons")
        with self.assertRaises(validate_subscriptions_contract.ContractError):
            validate_subscriptions_contract.validate_contract(payload)

    def test_reordered_or_replaced_capabilities_fail(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["billing", "subscriptions"]
        with self.assertRaises(validate_subscriptions_contract.ContractError):
            validate_subscriptions_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_subscriptions_contract.ContractError):
            validate_subscriptions_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
