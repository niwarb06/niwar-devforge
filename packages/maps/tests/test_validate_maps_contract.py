from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_maps_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_maps_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_maps_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_maps_contract)


class MapsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_maps_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_maps_contract.validate_contract(self.contract)

    def test_domain_and_baseline_capability(self) -> None:
        self.assertEqual(self.contract["domain"], "maps")
        self.assertEqual(self.contract["capabilities"], ["maps_adapter"])

    def test_provider_adapter_is_required(self) -> None:
        self.assertIs(self.contract["provider_adapter_required"], True)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("geocoding")
        with self.assertRaises(validate_maps_contract.ContractError):
            validate_maps_contract.validate_contract(payload)

    def test_wrong_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["live_tracking"]
        with self.assertRaises(validate_maps_contract.ContractError):
            validate_maps_contract.validate_contract(payload)

    def test_unknown_key_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["provider"] = "example"
        with self.assertRaises(validate_maps_contract.ContractError):
            validate_maps_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
