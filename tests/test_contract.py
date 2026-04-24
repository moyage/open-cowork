from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.contract import ContractValidationError, load_contract, validate_contract
from governance.simple_yaml import write_yaml


class ContractTests(unittest.TestCase):
    def test_invalid_contract_blocks_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.yaml"
            write_yaml(path, {"scope_in": ["src/**"]})
            errors = validate_contract({"scope_in": ["src/**"]})
            self.assertTrue(errors)
            with self.assertRaises(ContractValidationError):
                load_contract(path)

    def test_contract_requires_governance_guards(self):
        contract = {
            "objective": "bounded-governance-hardening",
            "scope_in": ["src/governance/**"],
            "scope_out": ["platformization"],
            "allowed_actions": ["edit-governance-runtime"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
            ],
            "validation_objects": ["StateConsistencyCheck"],
            "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
            "evidence_expectations": {"required": ["STATE_CONSISTENCY_CHECK.yaml"]},
        }
        errors = validate_contract(contract)
        self.assertTrue(errors)
        self.assertTrue(any("forbidden_actions missing required governance guards" in error for error in errors))

    def test_contract_rejects_scope_in_scope_out_conflicts(self):
        contract = {
            "objective": "bounded-governance-hardening",
            "scope_in": ["docs/**", ".governance/changes/CHG-1/evidence/**"],
            "scope_out": ["docs/archive/**", ".governance/changes/**"],
            "allowed_actions": ["edit_files"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["StateConsistencyCheck"],
            "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
            "evidence_expectations": {"required": ["changed_files_manifest"]},
        }

        errors = validate_contract(contract)

        self.assertTrue(any("scope_in conflicts with scope_out" in error for error in errors))
        self.assertTrue(any("docs/** overlaps docs/archive/**" in error for error in errors))
        self.assertTrue(any(".governance/changes/CHG-1/evidence/** overlaps .governance/changes/**" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
