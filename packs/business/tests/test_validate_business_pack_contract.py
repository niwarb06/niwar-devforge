from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_business_pack_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_business_pack_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_business_pack_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_business_pack_contract)


class BusinessPackContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_business_pack_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_business_pack_contract.validate_contract(self.contract)

    def test_pack_is_business(self) -> None:
        self.assertEqual(self.contract["pack"], "business")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(
            self.contract["capabilities"],
            ["crud", "dashboards", "reports", "roles", "export_import"],
        )

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = payload["capabilities"][:-1]
        with self.assertRaises(validate_business_pack_contract.ContractError):
            validate_business_pack_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("inventory")
        with self.assertRaises(validate_business_pack_contract.ContractError):
            validate_business_pack_contract.validate_contract(payload)

    def test_reordered_capabilities_fail(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = list(reversed(payload["capabilities"]))
        with self.assertRaises(validate_business_pack_contract.ContractError):
            validate_business_pack_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_business_pack_contract.ContractError):
            validate_business_pack_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
