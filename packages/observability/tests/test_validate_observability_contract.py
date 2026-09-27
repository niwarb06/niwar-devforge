from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_observability_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_observability_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_observability_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_observability_contract)


class ObservabilityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_observability_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_observability_contract.validate_contract(self.contract)

    def test_required_capabilities_are_present(self) -> None:
        self.assertEqual(
            set(self.contract["required_capabilities"]),
            {"structured_logging", "request_correlation"},
        )

    def test_duplicate_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["required_capabilities"].append("structured_logging")
        with self.assertRaises(validate_observability_contract.ContractError):
            validate_observability_contract.validate_contract(payload)

    def test_unknown_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["required_capabilities"].append("tracing")
        with self.assertRaises(validate_observability_contract.ContractError):
            validate_observability_contract.validate_contract(payload)

    def test_request_id_is_required_correlation_field(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["correlation_field"] = "trace_id"
        with self.assertRaises(validate_observability_contract.ContractError):
            validate_observability_contract.validate_contract(payload)

    def test_external_exporter_requirement_must_remain_disabled(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["external_exporter_required"] = True
        with self.assertRaises(validate_observability_contract.ContractError):
            validate_observability_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
