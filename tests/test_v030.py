from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index
from governance.simple_yaml import write_yaml
from governance.step_matrix import render_status_snapshot


class V030HumanParticipationTests(unittest.TestCase):
    def test_step5_status_points_to_current_approval_gate_and_exposes_gate_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-STATUS", current_step=5, status="step5-prepared")

            snapshot = render_status_snapshot(root, "CHG-V030-STATUS")

            self.assertEqual(snapshot["current_step"], 5)
            self.assertEqual(snapshot["next_decision"], "Step 5 / Approve the start")
            step5 = next(item for item in snapshot["step_progress"] if item["step"] == 5)
            self.assertEqual(step5["gate_type"], "approval-required")
            self.assertEqual(step5["gate_state"], "waiting-approval")
            self.assertEqual(step5["approval_state"], "required-pending")
            step4 = next(item for item in snapshot["step_progress"] if item["step"] == 4)
            self.assertEqual(step4["gate_type"], "review-required")
            self.assertEqual(step4["approval_state"], "not-required")

    def test_status_points_to_step9_after_step8_approval_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-STEP9-NEXT", current_step=8, status="review-approved")
            write_yaml(root / ".governance/changes/CHG-V030-STEP9-NEXT/human-gates.yaml", {
                "approvals": {
                    8: {"status": "approved", "approved_by": "human-sponsor"},
                },
            })

            snapshot = render_status_snapshot(root, "CHG-V030-STEP9-NEXT")

            self.assertEqual(snapshot["next_decision"], "Step 9 / Archive and carry forward")
            step8 = next(item for item in snapshot["step_progress"] if item["step"] == 8)
            self.assertEqual(step8["gate_state"], "approved")
            self.assertEqual(step8["approval_state"], "approved")
            step9 = next(item for item in snapshot["step_progress"] if item["step"] == 9)
            self.assertEqual(step9["approval_state"], "required-pending")

    def test_step_report_human_format_has_framework_agent_fields_and_short_confirmation_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-REPORT", current_step=5, status="step5-prepared")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "step",
                    "report",
                    "--change-id",
                    "CHG-V030-REPORT",
                    "--step",
                    "5",
                    "--format",
                    "human",
                ])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Step 5 / Approve the start", output)
            self.assertIn("framework_controls", output)
            self.assertIn("agent_actions_done", output)
            self.assertIn("agent_actions_expected", output)
            self.assertIn("approve", output)
            self.assertIn("revise", output)
            self.assertIn("reject", output)

    def test_step8_report_reads_recorded_human_gate_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-STEP8", current_step=8, status="step8-review-ready")
            change_dir = root / ".governance/changes/CHG-V030-STEP8"
            write_yaml(change_dir / "human-gates.yaml", {
                "approvals": {
                    8: {"status": "approved", "approved_by": "human-sponsor"},
                },
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "step",
                    "report",
                    "--change-id",
                    "CHG-V030-STEP8",
                    "--step",
                    "8",
                    "--format",
                    "human",
                ])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("- gate_state: approved", output)
            self.assertIn("- approval_state: approved", output)
            report = __import__("governance.simple_yaml", fromlist=["load_yaml"]).load_yaml(
                change_dir / "step-reports/step-8.yaml"
            )
            self.assertEqual(report["gate_state"], "approved")
            self.assertEqual(report["approval_state"], "approved")

    def test_step9_report_reads_recorded_human_gate_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-STEP9", current_step=9, status="step9-archive-ready")
            change_dir = root / ".governance/changes/CHG-V030-STEP9"
            write_yaml(change_dir / "human-gates.yaml", {
                "approvals": {
                    9: {"status": "approved", "approved_by": "human-sponsor"},
                },
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "step",
                    "report",
                    "--change-id",
                    "CHG-V030-STEP9",
                    "--step",
                    "9",
                    "--format",
                    "human",
                ])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("- gate_state: approved", output)
            self.assertIn("- approval_state: approved", output)
            report = __import__("governance.simple_yaml", fromlist=["load_yaml"]).load_yaml(
                change_dir / "step-reports/step-9.yaml"
            )
            self.assertEqual(report["gate_state"], "approved")
            self.assertEqual(report["approval_state"], "approved")

    def test_change_prepare_starts_at_step1_without_marking_step1_to_step5_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-V030-PREPARE", "--title", "Prepare semantics"])
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-V030-PREPARE",
                    "--goal",
                    "Prepare must not pretend Step 1 through Step 5 are complete",
                ])
            self.assertEqual(exit_code, 0)

            manifest = __import__("governance.simple_yaml", fromlist=["load_yaml"]).load_yaml(
                root / ".governance/changes/CHG-V030-PREPARE/manifest.yaml"
            )
            self.assertEqual(manifest["status"], "step1-ready")
            self.assertEqual(manifest["current_step"], 1)
            self.assertFalse(manifest["readiness"]["step6_entry_ready"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status_exit = main(["--root", str(root), "status"])
            self.assertEqual(status_exit, 0)
            output = stdout.getvalue()
            self.assertIn("current_step: 1", output)
            self.assertIn("completed_steps: none", output)
            self.assertIn("Step 5", output)
            self.assertIn("gate_type=approval-required", output)
            self.assertIn("gate_state=not-started", output)
            self.assertIn("approval_state=required-pending", output)
            self.assertIn("status=pending", output)

    def test_adopt_and_onboard_outputs_show_step5_step8_step9_human_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])

            adopt_stdout = io.StringIO()
            with contextlib.redirect_stdout(adopt_stdout):
                adopt_exit = main([
                    "--root",
                    str(root),
                    "adopt",
                    "--target",
                    str(root),
                    "--goal",
                    "Govern the next iteration",
                    "--dry-run",
                ])
            self.assertEqual(adopt_exit, 0)
            adopt_output = adopt_stdout.getvalue()
            self.assertIn("Step 5", adopt_output)
            self.assertIn("Step 8", adopt_output)
            self.assertIn("Step 9", adopt_output)

            onboard_stdout = io.StringIO()
            with contextlib.redirect_stdout(onboard_stdout):
                onboard_exit = main(["--root", str(root), "onboard", "--yes"])
            self.assertEqual(onboard_exit, 0)
            onboard_output = onboard_stdout.getvalue()
            self.assertIn("Step 5", onboard_output)
            self.assertIn("Step 8", onboard_output)
            self.assertIn("Step 9", onboard_output)

    def test_reviewer_mismatch_bypass_requires_human_readable_audit_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V030-BYPASS", current_step=7, status="step7-verified")
            change_dir = root / ".governance/changes/CHG-V030-BYPASS"
            write_yaml(change_dir / "verify.yaml", {
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
            })
            write_yaml(change_dir / "human-gates.yaml", {
                "approvals": {
                    8: {"status": "approved", "approved_by": "human-sponsor"},
                },
            })

            missing = io.StringIO()
            with contextlib.redirect_stdout(missing):
                missing_exit = main([
                    "--root", str(root),
                    "review",
                    "--change-id", "CHG-V030-BYPASS",
                    "--decision", "approve",
                    "--reviewer", "unexpected-reviewer",
                    "--rationale", "Mismatch should require audit fields",
                    "--allow-reviewer-mismatch",
                ])
            self.assertEqual(missing_exit, 1)
            self.assertIn("bypass reason", missing.getvalue())

            allowed = io.StringIO()
            with contextlib.redirect_stdout(allowed):
                allowed_exit = main([
                    "--root", str(root),
                    "review",
                    "--change-id", "CHG-V030-BYPASS",
                    "--decision", "approve",
                    "--reviewer", "unexpected-reviewer",
                    "--rationale", "Reviewed with explicit risk acceptance",
                    "--allow-reviewer-mismatch",
                    "--bypass-reason", "human accepted reviewer substitution",
                    "--bypass-recorded-by", "human-sponsor",
                    "--bypass-evidence-ref", "meeting-notes/reviewer-substitution.md",
                ])
            self.assertEqual(allowed_exit, 0)
            gates = __import__("governance.simple_yaml", fromlist=["load_yaml"]).load_yaml(change_dir / "human-gates.yaml")
            self.assertEqual(gates["bypasses"][0]["reason"], "human accepted reviewer substitution")
            self.assertEqual(gates["bypasses"][0]["recorded_by"], "human-sponsor")
            self.assertEqual(gates["bypasses"][0]["evidence_ref"], "meeting-notes/reviewer-substitution.md")
            review = __import__("governance.simple_yaml", fromlist=["load_yaml"]).load_yaml(change_dir / "review.yaml")
            self.assertEqual(
                review["trace"]["step8_approval_ref"],
                ".governance/changes/CHG-V030-BYPASS/human-gates.yaml#approvals.8",
            )

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "status": status,
            "current_step": current_step,
            "target_validation_objects": ["src/**", "tests/**"],
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "V0.3 human participation status semantics",
            "scope_in": ["src/**", "tests/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files", "run_commands"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["src/**", "tests/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["v030"]},
            "evidence_expectations": {"required": ["test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "1": {"owner": "human-sponsor", "gate": "review-required", "human_gate": False},
                "2": {"owner": "analyst-agent", "gate": "approval-required", "human_gate": True},
                "3": {"owner": "architect-agent", "gate": "review-required", "human_gate": False},
                "4": {"owner": "orchestrator-agent", "gate": "review-required", "human_gate": False},
                "5": {"owner": "human-sponsor", "gate": "approval-required", "human_gate": True},
                "6": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False},
                "7": {"owner": "verifier-agent", "gate": "review-required", "human_gate": False},
                "8": {"owner": "independent-reviewer", "gate": "approval-required", "human_gate": True},
                "9": {"owner": "maintainer-agent", "gate": "approval-required", "human_gate": True},
            },
        })
        write_yaml(change_dir / "human-gates.yaml", {
            "approvals": {
                2: {"status": "approved", "approved_by": "human-sponsor"},
            },
        })
        (change_dir / "tasks.md").write_text("# Tasks\n\nV0.3 human participation status semantics.\n", encoding="utf-8")
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {
                "change_id": change_id,
                "status": status,
                "current_step": current_step,
            },
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": status,
                "current_step": current_step,
            }],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
            "residual_followups": [],
        })


if __name__ == "__main__":
    unittest.main()
