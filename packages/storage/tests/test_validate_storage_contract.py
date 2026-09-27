from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_storage_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_storage_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_storage_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_storage_contract)


class StorageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_storage_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_storage_contract.validate_contract(self.contract)

    def test_all_baseline_capabilities_are_present(self) -> None:
        self.assertTrue(
            validate_storage_contract.REQUIRED_CAPABILITIES.issubset(
                set(self.contract["required_capabilities"])
            )
        )

    def test_duplicate_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["required_capabilities"].append(payload["required_capabilities"][0])
        with self.assertRaises(validate_storage_contract.ContractError):
            validate_storage_contract.validate_contract(payload)

    def test_missing_required_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["required_capabilities"].remove("signed_access")
        with self.assertRaises(validate_storage_contract.ContractError):
            validate_storage_contract.validate_contract(payload)

    def test_malformed_capability_name_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["required_capabilities"].append("Signed Access")
        with self.assertRaises(validate_storage_contract.ContractError):
            validate_storage_contract.validate_contract(payload)

    def test_unsupported_schema_version_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["schema_version"] = 2
        with self.assertRaises(validate_storage_contract.ContractError):
            validate_storage_contract.validate_contract(payload)

    def test_non_storage_module_identifier_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["module"] = "media"
        with self.assertRaises(validate_storage_contract.ContractError):
            validate_storage_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
