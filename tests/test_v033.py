from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index
from governance.simple_yaml import load_yaml, write_yaml


class V033GovernanceClosureTests(unittest.TestCase):
    def test_change_prepare_reports_scope_overlap_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V033-SCOPE", "--title", "Scope recovery")

            output = self._run_cli(
                root,
                "change",
                "prepare",
                "CHG-V033-SCOPE",
                "--goal",
                "show product recovery",
                "--scope-in",
                ".governance/**",
                expect=1,
            )

            self.assertIn("Cannot prepare change because scope_in overlaps scope_out.", output)
            self.assertIn(".governance/** overlaps .governance/archive/**", output)
            self.assertIn(".governance/changes/CHG-V033-SCOPE/**", output)
            self.assertNotIn("Traceback", output)

    def test_strict_step_gate_rejects_future_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_change(root, "CHG-V033-STRICT")

            output = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V033-STRICT",
                "--step",
                "5",
                "--approved-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("Step 5 cannot be approved yet", output)
            gates_path = root / ".governance/changes/CHG-V033-STRICT/human-gates.yaml"
            gates = load_yaml(gates_path) if gates_path.exists() else {"approvals": {}}
            self.assertNotIn(5, gates.get("approvals", {}))
            self.assertNotIn("5", gates.get("approvals", {}))

    def test_approval_token_policy_blocks_untrusted_text_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_change(root, "CHG-V033-TOKEN")
            policy = root / ".governance/changes/CHG-V033-TOKEN/approval-policy.yaml"
            write_yaml(policy, {
                "schema": "approval-policy/v1",
                "required": True,
                "token_sha256": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
            })

            output = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V033-TOKEN",
                "--step",
                "1",
                "--approved-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("trusted approval token is required", output)
            gates = load_yaml(root / ".governance/changes/CHG-V033-TOKEN/human-gates.yaml")
            self.assertEqual(gates.get("untrusted_attempts", [])[0]["step"], 1)
            self.assertNotIn(1, gates.get("approvals", {}))

            ok = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V033-TOKEN",
                "--step",
                "1",
                "--approved-by",
                "human-sponsor",
                "--approval-token",
                "secret",
            )
            self.assertIn("Step 1 approved", ok)

    def test_step_reports_project_intent_and_core_artifact_summary_without_python_repr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_change(root, "CHG-V033-REPORT")
            change_dir = root / ".governance/changes/CHG-V033-REPORT"
            self._write_confirmed_intent(change_dir)
            write_yaml(change_dir / "verify.yaml", {
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [{"name": "unit", "status": "pass"}],
                "issues": [],
            })
            write_yaml(change_dir / "review.yaml", {
                "decision": {"status": "approve", "rationale": "ready"},
                "reviewers": [{"role": "reviewer", "id": "hermes-agent"}],
                "runtime_evidence": {"runtime": "hermes", "invocation_status": "success"},
            })

            self._run_cli(root, "step", "report", "--change-id", "CHG-V033-REPORT", "--step", "3")
            self._run_cli(root, "step", "report", "--change-id", "CHG-V033-REPORT", "--step", "5")
            self._run_cli(root, "step", "report", "--change-id", "CHG-V033-REPORT", "--step", "8")

            step3 = (change_dir / "step-reports/step-3.md").read_text(encoding="utf-8")
            step5 = (change_dir / "step-reports/step-5.md").read_text(encoding="utf-8")
            step8 = (change_dir / "step-reports/step-8.md").read_text(encoding="utf-8")
            self.assertIn("project_intent: Ship v0.3.3 governance closure", step3)
            self.assertIn("## Artifact summary", step3)
            self.assertIn("design_summary", step3)
            self.assertIn("contract_scope_in", step5)
            self.assertIn("## Review gate vs decision", step8)
            self.assertIn("review_entry_gate: required-pending", step8)
            self.assertIn("review_decision: approve", step8)
            self.assertNotIn("{'role':", step8)

    def test_review_revise_records_structured_lifecycle_and_revise_imports_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V033-LIFECYCLE", current_step=7, status="step7-verified")
            change_dir = root / ".governance/changes/CHG-V033-LIFECYCLE"
            write_yaml(change_dir / "verify.yaml", {"summary": {"status": "pass", "blocker_count": 0}, "checks": [], "issues": []})
            write_yaml(change_dir / "human-gates.yaml", {"approvals": {8: {"status": "approved", "approved_by": "human-sponsor"}}})

            self._run_cli(
                root,
                "review",
                "--change-id",
                "CHG-V033-LIFECYCLE",
                "--decision",
                "revise",
                "--reviewer",
                "hermes-agent",
                "--rationale",
                "blocking: add dist/index.d.ts to materialized package",
                "--review-artifact-ref",
                "docs/reports/hermes-review.md",
            )
            lifecycle = load_yaml(change_dir / "review-lifecycle.yaml")
            self.assertEqual(lifecycle["rounds"][0]["decision"], "request_changes")
            self.assertIn("add dist/index.d.ts", lifecycle["rounds"][0]["blocking_findings"][0]["body"])

            self._run_cli(root, "revise", "--change-id", "CHG-V033-LIFECYCLE", "--reason", "address review", "--recorded-by", "codex")
            lifecycle = load_yaml(change_dir / "review-lifecycle.yaml")
            revision = load_yaml(change_dir / "revision-history.yaml")
            self.assertEqual(lifecycle["rework_rounds"][0]["status"], "revision-open")
            self.assertEqual(revision["revisions"][0]["findings"][0]["source"], "review-lifecycle.yaml")

    def test_archived_step9_report_is_closeout_panel_not_waiting_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V033-ARCHIVE", current_step=8, status="review-approved")
            change_dir = root / ".governance/changes/CHG-V033-ARCHIVE"
            write_yaml(change_dir / "review.yaml", {"decision": {"status": "approve", "rationale": "ready"}})
            write_yaml(change_dir / "verify.yaml", {"summary": {"status": "pass", "blocker_count": 0}, "checks": [], "issues": []})
            write_yaml(change_dir / "human-gates.yaml", {"approvals": {
                8: {"status": "approved", "approved_by": "human-sponsor"},
                9: {"status": "approved", "approved_by": "human-sponsor"},
            }})

            self._run_cli(root, "archive", "--change-id", "CHG-V033-ARCHIVE")

            step9 = (root / ".governance/archive/CHG-V033-ARCHIVE/step-reports/step-9.md").read_text(encoding="utf-8")
            self.assertIn("Archive is complete", step9)
            self.assertIn("archive_destination", step9)
            self.assertIn("review_decision: approve", step9)
            self.assertNotIn("Wait for a human approve / revise / reject", step9)
            self.assertNotIn("Pause for human confirmation before advancing.", step9)

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output

    def _prepare_change(self, root: Path, change_id: str) -> None:
        self._run_cli(root, "init")
        self._run_cli(root, "change", "create", change_id, "--title", change_id)
        self._run_cli(root, "change", "prepare", change_id, "--goal", "v0.3.3 closure")

    def _write_confirmed_intent(self, change_dir: Path) -> None:
        write_yaml(change_dir / "intent-confirmation.yaml", {
            "schema": "intent-confirmation/v1",
            "change_id": change_dir.name,
            "status": "confirmed",
            "project_intent": "Ship v0.3.3 governance closure",
            "requirements": ["strict gates", "decision-grade reports"],
            "scope_in": ["src/**", "tests/**"],
            "scope_out": [".governance/archive/**"],
            "acceptance_criteria": ["reports show intent"],
            "risks": ["agent shortcutting"],
            "open_questions": [],
        })

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {"step6_entry_ready": current_step >= 6, "missing_items": []},
            "target_validation_objects": ["src/governance/review.py"],
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "v0.3.3 closure",
            "scope_in": ["src/**", "tests/**", f".governance/changes/{change_id}/evidence/**"],
            "scope_out": [".governance/archive/**", ".governance/runtime/**"],
            "allowed_actions": ["edit_files", "run_commands", "write_evidence"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["src/governance/review.py"],
            "verification": {"commands": ["python3 -m unittest discover -s tests"], "checks": ["v033"]},
            "evidence_expectations": {"required": ["command_output", "test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "5": {"owner": "human-sponsor", "human_gate": True, "gate": "approval-required"},
                "6": {"owner": "codex-agent", "human_gate": False, "gate": "execution"},
                "7": {"owner": "verifier-agent", "human_gate": False, "gate": "verify"},
                "8": {"owner": "hermes-agent", "reviewer": "hermes-agent", "human_gate": True, "gate": "review-entry"},
                "9": {"owner": "maintainer-agent", "reviewer": "human-sponsor", "human_gate": True, "gate": "archive"},
            }
        })
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step},
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })


if __name__ == "__main__":
    unittest.main()
