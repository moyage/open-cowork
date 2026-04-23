from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.simple_yaml import write_yaml
from governance.step_matrix import render_step_matrix


class StepMatrixTests(unittest.TestCase):
    def test_step_matrix_contains_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_dir = root / ".governance/changes/CHG-1"
            index_dir = root / ".governance/index"
            change_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "manifest.yaml", {
                "id": "CHG-1",
                "status": "step6-executed-pre-step7",
                "formal_dispatch_status": "completed",
                "stage_mode": "step6-executed-pre-step7",
                "roles": {"executor": "OOSO/OpenCode", "formal_orchestrator": "Hermes", "reviewer": "Hermes"},
                "target_validation_objects": [
                    "FlowOverviewAndActionGuide",
                    "ProgressVisibilityAndHumanInterventionPoints",
                ],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "flow-clarity-progress-visibility-bounded-enhancement",
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
                    "FlowOverviewAndActionGuide",
                    "ProgressVisibilityAndHumanInterventionPoints",
                ],
                "verification": {"checks": ["state-consistency"], "commands": ["python -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "5": {"owner": "Marvis", "gate": "approval-required"},
                    "6": {"owner": "OOSO/OpenCode", "gate": "auto-pass"},
                    "8": {"owner": "Hermes", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nImplement bounded governance flow visibility enhancement.\n", encoding="utf-8")
            write_yaml(index_dir / "current-change.yaml", {
                "current_change_id": "CHG-1",
                "current_step": 6,
                "status": "step6-executed-pre-step7",
                "formal_dispatch_status": "completed",
            })
            write_yaml(index_dir / "changes-index.yaml", {
                "changes": [{"id": "CHG-1", "status": "step6-executed-pre-step7", "formal_dispatch_status": "completed"}],
            })
            write_yaml(index_dir / "maintenance-status.yaml", {
                "status": "step6-executed-pre-step7",
                "current_change_active": "step6-executed-pre-step7",
                "current_change_id": "CHG-1",
            })

            matrix = render_step_matrix(root, "CHG-1")

            self.assertEqual(matrix["total_steps"], 9)
            self.assertEqual(matrix["current_step"], 6)
            self.assertEqual(matrix["current_status"], "step6-executed-pre-step7")
            self.assertEqual(matrix["owner_or_stage_actor"], "OOSO/OpenCode")
            self.assertEqual(matrix["current_flow_section"], "Execute and verify")
            self.assertEqual(matrix["next_step"], 7)
            self.assertTrue(matrix["human_intervention_points"])
            self.assertTrue(matrix["action_guide"])
            self.assertTrue(matrix["expected_outputs"])
            self.assertEqual(matrix["blockers"], [])
            self.assertEqual(matrix["validation_objects"], [
                "FlowOverviewAndActionGuide",
                "ProgressVisibilityAndHumanInterventionPoints",
            ])
            self.assertTrue(any(item.startswith("validation_object:") for item in matrix["expected_outputs"]))


if __name__ == "__main__":
    unittest.main()
