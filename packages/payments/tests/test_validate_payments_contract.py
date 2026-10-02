from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_payments_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_payments_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_payments_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_payments_contract)


class PaymentsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_payments_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_payments_contract.validate_contract(self.contract)

    def test_domain_is_payments(self) -> None:
        self.assertEqual(self.contract["domain"], "payments")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(
            self.contract["capabilities"],
            ["payments_adapter"],
        )

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].remove("payments_adapter")
        with self.assertRaises(validate_payments_contract.ContractError):
            validate_payments_contract.validate_contract(payload)

    def test_reordered_or_replaced_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["webhook_processing"]
        with self.assertRaises(validate_payments_contract.ContractError):
            validate_payments_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("refunds_interface")
        with self.assertRaises(validate_payments_contract.ContractError):
            validate_payments_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_payments_contract.ContractError):
            validate_payments_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
