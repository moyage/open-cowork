from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.simple_yaml import write_yaml
from governance.state_consistency import evaluate_state_consistency


class StateConsistencyTests(unittest.TestCase):
    def test_aligned_live_shape_returns_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_dir = root / ".governance/changes/CHG-1"
            index_dir = root / ".governance/index"
            change_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "manifest.yaml", {
                "id": "CHG-1",
                "status": "architect-drafted",
                "formal_dispatch_status": "pending",
                "stage_mode": "architect-draft",
                "roles": {"executor": "OOSO/OpenCode", "reviewer": "Hermes"},
                "target_validation_objects": [
                    "StateConsistencyCheck",
                    "StepMatrixView",
                    "PostRoundRetrospectiveAndIterationSynthesis",
                ],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "bounded-governance-hardening",
                "scope_in": ["src/governance/**"],
                "scope_out": ["platformization"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": [
                    "StateConsistencyCheck",
                    "StepMatrixView",
                    "PostRoundRetrospectiveAndIterationSynthesis",
                ],
                "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
                "evidence_expectations": {"required": ["STATE_CONSISTENCY_CHECK.yaml"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "OOSO/OpenCode", "gate": "auto-pass"},
                    "8": {"owner": "Hermes", "gate": "approval-required"},
                },
            })
            write_yaml(index_dir / "current-change.yaml", {
                "current_change_id": "CHG-1",
                "current_step": "draft",
                "status": "architect-drafted",
                "formal_dispatch_status": "pending",
            })
            write_yaml(index_dir / "changes-index.yaml", {
                "changes": [{"id": "CHG-1", "status": "architect-drafted", "formal_dispatch_status": "pending"}],
            })
            write_yaml(index_dir / "maintenance-status.yaml", {
                "status": "architect-draft-pending-dispatch",
                "current_change_active": "draft",
                "current_change_id": "CHG-1",
            })

            result = evaluate_state_consistency(root, "CHG-1")

            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["summary"]["blocker_count"], 0)

    def test_identifier_drift_returns_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_dir = root / ".governance/changes/CHG-1"
            index_dir = root / ".governance/index"
            change_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "manifest.yaml", {
                "id": "CHG-1",
                "status": "architect-drafted",
                "formal_dispatch_status": "pending",
                "stage_mode": "architect-draft",
                "roles": {"executor": "OOSO/OpenCode", "reviewer": "Hermes"},
                "target_validation_objects": [
                    "StateConsistencyCheck",
                    "StepMatrixView",
                    "PostRoundRetrospectiveAndIterationSynthesis",
                ],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "bounded-governance-hardening",
                "scope_in": ["src/governance/**"],
                "scope_out": ["platformization"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": [
                    "StateConsistencyCheck",
                    "StepMatrixView",
                    "PostRoundRetrospectiveAndIterationSynthesis",
                ],
                "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
                "evidence_expectations": {"required": ["STATE_CONSISTENCY_CHECK.yaml"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "OOSO/OpenCode", "gate": "auto-pass"},
                    "8": {"owner": "Hermes", "gate": "approval-required"},
                },
            })
            write_yaml(index_dir / "current-change.yaml", {
                "current_change_id": "CHG-9",
                "current_step": "draft",
                "status": "architect-drafted",
                "formal_dispatch_status": "pending",
            })
            write_yaml(index_dir / "changes-index.yaml", {
                "changes": [{"id": "CHG-1", "status": "architect-drafted", "formal_dispatch_status": "pending"}],
            })
            write_yaml(index_dir / "maintenance-status.yaml", {
                "status": "architect-draft-pending-dispatch",
                "current_change_active": "draft",
                "current_change_id": "CHG-1",
            })

            result = evaluate_state_consistency(root, "CHG-1")

            self.assertEqual(result["status"], "blocker")
            self.assertGreater(result["summary"]["blocker_count"], 0)

    def test_executor_and_reviewer_merge_returns_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_dir = root / ".governance/changes/CHG-1"
            index_dir = root / ".governance/index"
            change_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "manifest.yaml", {
                "id": "CHG-1",
                "status": "step6-ready",
                "formal_dispatch_status": "completed",
                "stage_mode": "step6-ready",
                "roles": {"executor": "SharedActor", "reviewer": "SharedActor"},
                "target_validation_objects": ["StateConsistencyCheck"],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "bounded-governance-hardening",
                "scope_in": ["src/governance/**"],
                "scope_out": ["platformization"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
                "evidence_expectations": {"required": ["STATE_CONSISTENCY_CHECK.yaml"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "SharedActor", "gate": "auto-pass"},
                    "8": {"owner": "SharedActor", "gate": "approval-required"},
                },
            })
            write_yaml(index_dir / "current-change.yaml", {
                "current_change_id": "CHG-1",
                "current_step": 6,
                "status": "step6-ready",
                "formal_dispatch_status": "completed",
            })
            write_yaml(index_dir / "changes-index.yaml", {
                "changes": [{"id": "CHG-1", "status": "step6-ready", "formal_dispatch_status": "completed"}],
            })
            write_yaml(index_dir / "maintenance-status.yaml", {
                "status": "step6-ready",
                "current_change_active": "step6-ready",
                "current_change_id": "CHG-1",
            })

            result = evaluate_state_consistency(root, "CHG-1")

            self.assertEqual(result["status"], "blocker")
            self.assertTrue(any(check["name"] == "execution_review_owner_separation" and check["status"] == "blocker" for check in result["checks"]))


if __name__ == "__main__":
    unittest.main()
