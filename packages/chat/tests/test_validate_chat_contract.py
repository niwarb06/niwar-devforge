from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_chat_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_chat_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_chat_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_chat_contract)


class ChatContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validate_chat_contract.load_contract()

    def test_committed_contract_is_valid(self) -> None:
        validate_chat_contract.validate_contract(self.contract)

    def test_domain_and_baseline_capability(self) -> None:
        self.assertEqual(self.contract["domain"], "chat")
        self.assertEqual(self.contract["capabilities"], ["realtime_events"])

    def test_provider_adapter_is_required(self) -> None:
        self.assertIs(self.contract["provider_adapter_required"], True)

    def test_extra_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"].append("chat_messaging")
        with self.assertRaises(validate_chat_contract.ContractError):
            validate_chat_contract.validate_contract(payload)

    def test_wrong_capability_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["capabilities"] = ["chat_messaging"]
        with self.assertRaises(validate_chat_contract.ContractError):
            validate_chat_contract.validate_contract(payload)

    def test_unknown_key_fails(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["transport"] = "websocket"
        with self.assertRaises(validate_chat_contract.ContractError):
            validate_chat_contract.validate_contract(payload)


if __name__ == "__main__":
    unittest.main()
