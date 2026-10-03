from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_delivery_logistics_pack_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_delivery_logistics_pack_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_delivery_logistics_pack_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_delivery_logistics_pack_contract)


class DeliveryLogisticsPackContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_delivery_logistics_pack_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_delivery_logistics_pack_contract.validate_contract(self.contract)

    def test_pack_is_delivery_logistics(self) -> None:
        self.assertEqual(self.contract["pack"], "delivery-logistics")

    def test_baseline_capabilities_are_exact(self) -> None:
        self.assertEqual(
            self.contract["capabilities"],
            [
                "orders",
                "driver_courier_state",
                "assignment",
                "route_location",
                "proof_of_delivery",
            ],
        )

    def test_missing_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = payload["capabilities"][:-1]
        with self.assertRaises(validate_delivery_logistics_pack_contract.ContractError):
            validate_delivery_logistics_pack_contract.validate_contract(payload)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("dispatch_pricing")
        with self.assertRaises(validate_delivery_logistics_pack_contract.ContractError):
            validate_delivery_logistics_pack_contract.validate_contract(payload)

    def test_reordered_capabilities_fail(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = list(reversed(payload["capabilities"]))
        with self.assertRaises(validate_delivery_logistics_pack_contract.ContractError):
            validate_delivery_logistics_pack_contract.validate_contract(payload)

    def test_unknown_contract_field_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_delivery_logistics_pack_contract.ContractError):
            validate_delivery_logistics_pack_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
