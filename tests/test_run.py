from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.change_package import create_change_package
from governance.evidence import MissingEvidenceError
from governance.index import ensure_governance_index
from governance.run import AdapterRequest, run_change
from governance.simple_yaml import load_yaml, write_yaml


class RunTests(unittest.TestCase):
    def test_run_writes_evidence_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-3")
            contract_path = root / ".governance/changes/CHG-3/contract.yaml"
            write_yaml(contract_path, {
                "objective": "bounded-governance-hardening",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["create_code"],
                "forbidden_actions": [
                    "bypass_verify_review_archive",
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": [], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            manifest_path = root / ".governance/changes/CHG-3/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(manifest_path, manifest)
            write_yaml(root / ".governance/changes/CHG-3/bindings.yaml", {
                "steps": {
                    "6": {"owner": "OOSO/OpenCode", "gate": "auto-pass"},
                    "8": {"owner": "Hermes", "gate": "approval-required"},
                },
            })
            response = run_change(root, AdapterRequest(
                change_id="CHG-3",
                contract_path=str(contract_path),
                working_directory=str(root),
                allowed_write_scope=[".governance/**", "src/**", "tests/**"],
                timeout_seconds=60,
                command="python -m unittest",
                command_output="ok",
                test_output="4 tests passed",
                artifacts={"created": ["src/governance/index.py"], "modified": ["tests/test_run.py"]},
            ))
            evidence_dir = root / ".governance/changes/CHG-3/evidence"
            self.assertTrue((evidence_dir / "execution-summary.yaml").exists())
            manifest = load_yaml(evidence_dir / "changed-files-manifest.yaml")
            self.assertIn("src/governance/index.py", manifest["created"])
            self.assertTrue(response.completed)
            self.assertIn("evidence/execution-summary.yaml", response.evidence_refs)

    def test_missing_required_evidence_blocks_completion(self):
        with self.assertRaises(MissingEvidenceError):
            from governance.evidence import ensure_required_evidence

            ensure_required_evidence(["missing_item"], {})

    def test_run_accepts_descriptive_contract_evidence_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-4")
            contract_path = root / ".governance/changes/CHG-4/contract.yaml"
            write_yaml(contract_path, {
                "objective": "bounded-governance-hardening",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["create_code"],
                "forbidden_actions": [
                    "bypass_verify_review_archive",
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck", "StepMatrixView", "PostRoundRetrospectiveAndIterationSynthesis"],
                "verification": {"commands": ["python3 -m unittest discover -s tests"], "checks": ["bounded evidence persisted"]},
                "evidence_expectations": {"required": [
                    "machine-readable StateConsistencyCheck result covering manifest, current-change, changes-index, and maintenance-status",
                    "human-readable StepMatrixView output for the active change",
                    "minimal retrospective and iteration synthesis artifacts generated after archive",
                    "verification evidence showing the bounded tests or checks executed successfully",
                ]},
            })
            change_dir = root / ".governance/changes/CHG-4"
            manifest_path = change_dir / "manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(manifest_path, manifest)
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "OOSO/OpenCode", "gate": "auto-pass"},
                    "8": {"owner": "Hermes", "gate": "approval-required"},
                },
            })
            (change_dir / "STATE_CONSISTENCY_CHECK.yaml").write_text("status: pass\n", encoding="utf-8")
            (change_dir / "STEP_MATRIX_VIEW.md").write_text("# Step Matrix\n", encoding="utf-8")
            (change_dir / "POST_ROUND_RETROSPECTIVE_AND_ITERATION_SYNTHESIS.yaml").write_text("status: generated\n", encoding="utf-8")
            response = run_change(root, AdapterRequest(
                change_id="CHG-4",
                contract_path=str(contract_path),
                working_directory=str(root),
                allowed_write_scope=[".governance/**", "src/**", "tests/**"],
                timeout_seconds=60,
                command="python3 -m unittest discover -s tests",
                command_output="ok",
                test_output="13 tests passed",
                artifacts={"created": [], "modified": []},
                evidence_refs=[
                    "STATE_CONSISTENCY_CHECK.yaml",
                    "STEP_MATRIX_VIEW.md",
                    "POST_ROUND_RETROSPECTIVE_AND_ITERATION_SYNTHESIS.yaml",
                ],
            ))

            self.assertTrue(response.completed)

    def test_evidence_written_under_change_evidence_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-5")
            contract_path = root / ".governance/changes/CHG-5/contract.yaml"
            write_yaml(contract_path, {
                "objective": "bounded-governance-hardening",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["create_code"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": [], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            manifest_path = root / ".governance/changes/CHG-5/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(manifest_path, manifest)
            write_yaml(root / ".governance/changes/CHG-5/bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor", "gate": "auto-pass"},
                    "8": {"owner": "reviewer", "gate": "approval-required"},
                },
            })
            response = run_change(root, AdapterRequest(
                change_id="CHG-5",
                contract_path=str(contract_path),
                working_directory=str(root),
                allowed_write_scope=[".governance/**", "src/**", "tests/**"],
                timeout_seconds=60,
                command="python -m unittest",
                command_output="ok",
                test_output="tests passed",
                artifacts={"created": ["src/example.py"], "modified": []},
            ))
            self.assertTrue(response.completed)
            evidence_dir = root / ".governance/changes/CHG-5/evidence"
            self.assertTrue((evidence_dir / "execution-summary.yaml").exists())
            self.assertTrue((evidence_dir / "changed-files-manifest.yaml").exists())

    def test_run_blocks_when_step7_verifier_matches_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-6")
            contract_path = root / ".governance/changes/CHG-6/contract.yaml"
            write_yaml(contract_path, {
                "objective": "enforce-verifier-separation",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["create_code"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": [], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            manifest_path = root / ".governance/changes/CHG-6/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(manifest_path, manifest)
            write_yaml(root / ".governance/changes/CHG-6/bindings.yaml", {
                "steps": {
                    "6": {"owner": "shared-actor", "gate": "auto-pass"},
                    "7": {"owner": "shared-actor", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })

            with self.assertRaisesRegex(ValueError, "verification owner"):
                run_change(root, AdapterRequest(
                    change_id="CHG-6",
                    contract_path=str(contract_path),
                    working_directory=str(root),
                    allowed_write_scope=[".governance/**", "src/**", "tests/**"],
                    timeout_seconds=60,
                    command="python -m unittest",
                    command_output="ok",
                    test_output="tests passed",
                    artifacts={"created": ["src/example.py"], "modified": []},
                ))

    def test_run_blocks_when_artifacts_escape_allowed_write_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            create_change_package(root, "CHG-7")
            contract_path = root / ".governance/changes/CHG-7/contract.yaml"
            write_yaml(contract_path, {
                "objective": "enforce-write-boundary",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["create_code"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": [], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            manifest_path = root / ".governance/changes/CHG-7/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(manifest_path, manifest)
            write_yaml(root / ".governance/changes/CHG-7/bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })

            with self.assertRaisesRegex(ValueError, "outside the allowed write boundary"):
                run_change(root, AdapterRequest(
                    change_id="CHG-7",
                    contract_path=str(contract_path),
                    working_directory=str(root),
                    allowed_write_scope=[".governance/**", "src/**", "tests/**"],
                    timeout_seconds=60,
                    command="python -m unittest",
                    command_output="ok",
                    test_output="tests passed",
                    artifacts={"created": ["docs/README.md"], "modified": []},
                ))


if __name__ == "__main__":
    unittest.main()
