from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_notifications_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_notifications_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_notifications_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_notifications_contract)


class NotificationsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_notifications_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_notifications_contract.validate_contract(self.contract)

    def test_domain_is_notifications(self) -> None:
        self.assertEqual(self.contract["domain"], "notifications")

    def test_baseline_capability_is_push_notifications(self) -> None:
        self.assertEqual(self.contract["capabilities"], ["push_notifications"])

    def test_provider_adapter_is_required(self) -> None:
        self.assertIs(self.contract["provider_adapter_required"], True)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("email")
        with self.assertRaises(validate_notifications_contract.ContractError):
            validate_notifications_contract.validate_contract(payload)

    def test_provider_adapter_false_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider_adapter_required"] = False
        with self.assertRaises(validate_notifications_contract.ContractError):
            validate_notifications_contract.validate_contract(payload)

    def test_unknown_key_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["delivery_state"] = "sent"
        with self.assertRaises(validate_notifications_contract.ContractError):
            validate_notifications_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
