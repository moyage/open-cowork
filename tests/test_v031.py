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


class V031HumanRuntimeTests(unittest.TestCase):
    def test_intent_only_step_reports_work_before_prepare_and_do_not_claim_step5(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--root", str(root), "init"]), 0)
                self.assertEqual(main(["--root", str(root), "change", "create", "CHG-V031-INTENT", "--title", "Intent only"]), 0)

            manifest = load_yaml(root / ".governance/changes/CHG-V031-INTENT/manifest.yaml")
            self.assertEqual(manifest["current_step"], 1)

            capture_stdout = io.StringIO()
            with contextlib.redirect_stdout(capture_stdout):
                exit_code = main([
                    "--root", str(root),
                    "intent", "capture",
                    "--change-id", "CHG-V031-INTENT",
                    "--project-intent", "Make Step 1 visible before prepare",
                    "--requirement", "Show requirements before contract exists",
                    "--scope-in", "src/governance/**",
                    "--scope-out", "dist/**",
                    "--acceptance", "human can read Step 1",
                    "--risk", "contract is not ready yet",
                    "--open-question", "Should Step 2 also render early?",
                ])
            self.assertEqual(exit_code, 0)
            self.assertIn("Step 1 report", capture_stdout.getvalue())

            report_stdout = io.StringIO()
            with contextlib.redirect_stdout(report_stdout):
                exit_code = main([
                    "--root", str(root),
                    "step", "report",
                    "--change-id", "CHG-V031-INTENT",
                    "--step", "1",
                    "--format", "human",
                ])
            output = report_stdout.getvalue()
            self.assertEqual(exit_code, 0, output)
            self.assertIn("Make Step 1 visible before prepare", output)
            self.assertIn("Show requirements before contract exists", output)
            self.assertIn("dist/**", output)
            self.assertNotIn("Step report failed", output)

            manifest = load_yaml(root / ".governance/changes/CHG-V031-INTENT/manifest.yaml")
            self.assertEqual(manifest["current_step"], 1)
            self.assertIn(manifest["status"], {"drafting", "intent-captured", "awaiting-intent-confirmation", "step1-ready"})

    def test_natural_status_commands_project_existing_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_change(root, "CHG-V031-STATUS")

            intent_stdout = self._run_cli(root, "intent", "status", "--change-id", "CHG-V031-STATUS", "--format", "human")
            self.assertIn("Intent status", intent_stdout)
            self.assertIn("confirmed", intent_stdout)
            self.assertIn("Govern status commands", intent_stdout)

            participants_stdout = self._run_cli(root, "participants", "list", "--change-id", "CHG-V031-STATUS", "--format", "human")
            self.assertIn("Participants", participants_stdout)
            self.assertIn("Step 8", participants_stdout)
            self.assertIn("independent-reviewer", participants_stdout)

            change_stdout = self._run_cli(root, "change", "status", "--change-id", "CHG-V031-STATUS", "--format", "human")
            self.assertIn("Change status", change_stdout)
            self.assertIn("current_step: 1", change_stdout)
            self.assertIn("step1-ready", change_stdout)

            status_stdout = self._run_cli(root, "status", "--change-id", "CHG-V031-STATUS")
            self.assertIn("Human status snapshot", status_stdout)
            self.assertIn("current_step: 1", status_stdout)

    def test_status_last_archive_summarizes_closeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            archive_dir = root / ".governance/archive/CHG-V031-ARCHIVE"
            archive_dir.mkdir(parents=True)
            write_yaml(root / ".governance/index/current-change.yaml", {"schema": "current-change/v1", "change_id": None, "status": "idle", "current_step": None})
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "last_archived_change": "CHG-V031-ARCHIVE",
                "last_archive_at": "2026-04-27T00:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": "CHG-V031-ARCHIVE",
                    "archive_path": ".governance/archive/CHG-V031-ARCHIVE/",
                    "archived_at": "2026-04-27T00:00:00+00:00",
                    "receipt": ".governance/archive/CHG-V031-ARCHIVE/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True, "change_id": "CHG-V031-ARCHIVE"})
            write_yaml(archive_dir / "review.yaml", {"decision": {"status": "approve", "rationale": "ready"}})
            write_yaml(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml", {
                "status": "pass",
                "human_gate_summary": {
                    5: {"status": "approved", "approved_by": "human"},
                    8: {"status": "approved", "approved_by": "human"},
                    9: {"status": "approved", "approved_by": "human"},
                },
            })

            output = self._run_cli(root, "status", "--last-archive")
            self.assertIn("Last archived closeout", output)
            self.assertIn("CHG-V031-ARCHIVE", output)
            self.assertIn("review_decision: approve", output)
            self.assertIn("final_consistency: pass", output)
            self.assertIn("Step 5", output)
            self.assertIn("Step 8", output)
            self.assertIn("Step 9", output)

    def test_step_reports_aggregate_evidence_and_reviewer_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V031-EVIDENCE", current_step=8, status="review-approved")
            change_dir = root / ".governance/changes/CHG-V031-EVIDENCE"
            evidence_dir = change_dir / "evidence"
            evidence_dir.mkdir(exist_ok=True)
            write_yaml(evidence_dir / "execution-summary.yaml", {
                "status": "success",
                "run_id": "run-v031",
                "artifacts": {"created": ["src/governance/status_views.py"], "modified": ["src/governance/step_report.py"]},
                "evidence_refs": ["docs/reports/runtime.md"],
            })
            write_yaml(evidence_dir / "command-output-summary.yaml", {"command": "python3 -m unittest", "summary": "all commands completed"})
            write_yaml(evidence_dir / "test-output-summary.yaml", {"summary": "Ran 99 tests OK"})
            write_yaml(evidence_dir / "changed-files-manifest.yaml", {"created": ["src/governance/status_views.py"], "modified": ["src/governance/step_report.py"]})
            write_yaml(change_dir / "verify.yaml", {
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [{"name": "state-consistency", "status": "pass", "ref": "STATE_CONSISTENCY_CHECK.yaml"}],
                "issues": [],
            })
            write_yaml(change_dir / "review.yaml", {
                "reviewers": [{"role": "reviewer", "id": "hermes-reviewer"}],
                "decision": {"status": "approve", "rationale": "approved with runtime evidence"},
                "conditions": {"must_before_next_step": [], "followups": ["document release notes"]},
                "runtime_evidence": {
                    "runtime": "hermes",
                    "health_check": "pass",
                    "invocation_status": "success",
                    "review_artifact_ref": "docs/reports/hermes-review.md",
                },
            })

            step6 = self._run_cli(root, "step", "report", "--change-id", "CHG-V031-EVIDENCE", "--step", "6", "--format", "human")
            self.assertIn("run-v031", step6)
            self.assertIn("Ran 99 tests OK", step6)
            self.assertIn("src/governance/status_views.py", step6)

            step7 = self._run_cli(root, "step", "report", "--change-id", "CHG-V031-EVIDENCE", "--step", "7", "--format", "human")
            self.assertIn("verify_status: pass", step7)
            self.assertIn("state-consistency", step7)

            step8 = self._run_cli(root, "step", "report", "--change-id", "CHG-V031-EVIDENCE", "--step", "8", "--format", "human")
            self.assertIn("review_decision: approve", step8)
            self.assertIn("runtime: hermes", step8)
            self.assertIn("review_artifact_ref: docs/reports/hermes-review.md", step8)

    def test_step_approvals_refresh_reports_and_clean_readiness_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_change(root, "CHG-V031-APPROVAL-REFRESH")
            change_dir = root / ".governance/changes/CHG-V031-APPROVAL-REFRESH"

            # Prepare may still need explicit Step 1 human confirmation, but it
            # must not keep claiming that confirmed intent itself is missing.
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertNotIn("intent_confirmation", manifest["readiness"]["missing_items"])
            self.assertIn("step1_confirmation", manifest["readiness"]["missing_items"])

            self._run_cli(
                root,
                "step", "approve",
                "--change-id", "CHG-V031-APPROVAL-REFRESH",
                "--step", "1",
                "--approved-by", "human-sponsor",
            )
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertNotIn("step1_confirmation", manifest["readiness"]["missing_items"])
            step1 = load_yaml(change_dir / "step-reports/step-1.yaml")
            self.assertEqual(step1["gate_state"], "reviewed")

            # A stored report rendered before approval must be refreshed by the
            # approval command rather than left as a stale blocker for handoff.
            self._run_cli(root, "step", "report", "--change-id", "CHG-V031-APPROVAL-REFRESH", "--step", "2")
            self._run_cli(
                root,
                "step", "approve",
                "--change-id", "CHG-V031-APPROVAL-REFRESH",
                "--step", "2",
                "--approved-by", "human-sponsor",
            )
            step2 = load_yaml(change_dir / "step-reports/step-2.yaml")
            self.assertEqual(step2["gate_state"], "approved")
            self.assertEqual(step2["approval_state"], "approved")
            step2_md = (change_dir / "step-reports/step-2.md").read_text(encoding="utf-8")
            self.assertIn("gate_state: approved", step2_md)
            self.assertIn("approval_state: approved", step2_md)

    def test_review_revise_reopens_revision_loop_and_records_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V031-REVISE", current_step=7, status="step7-verified")
            change_dir = root / ".governance/changes/CHG-V031-REVISE"
            write_yaml(change_dir / "verify.yaml", {"summary": {"status": "pass", "blocker_count": 0}, "checks": [], "issues": []})
            write_yaml(change_dir / "human-gates.yaml", {"approvals": {5: {"status": "approved", "approved_by": "human"}, 8: {"status": "approved", "approved_by": "human"}}})

            review_output = self._run_cli(root, "review", "--change-id", "CHG-V031-REVISE", "--decision", "revise", "--reviewer", "independent-reviewer", "--rationale", "needs a fix")
            self.assertIn("review-revise", review_output)

            revise_output = self._run_cli(root, "revise", "--change-id", "CHG-V031-REVISE", "--reason", "address reviewer finding", "--recorded-by", "codex")
            self.assertIn("Revision opened", revise_output)
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertEqual(manifest["status"], "revision-open")
            self.assertEqual(manifest["current_step"], 6)
            revision = load_yaml(change_dir / "revision-history.yaml")
            self.assertEqual(revision["revisions"][0]["revision_round"], 1)

            run_output = self._run_cli(
                root,
                "run",
                "--change-id", "CHG-V031-REVISE",
                "--command", "apply revision",
                "--command-output", "revision command succeeded",
                "--test-output", "revision tests passed",
                "--modified", "src/governance/revision.py",
            )
            self.assertIn("Run completed", run_output)

    def test_review_command_records_runtime_evidence_and_default_scope_out_has_noise_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V031-RUNTIME", current_step=7, status="step7-verified")
            change_dir = root / ".governance/changes/CHG-V031-RUNTIME"
            write_yaml(change_dir / "verify.yaml", {"summary": {"status": "pass", "blocker_count": 0}, "checks": [], "issues": []})
            write_yaml(change_dir / "human-gates.yaml", {"approvals": {8: {"status": "approved", "approved_by": "human"}}})

            self._run_cli(
                root,
                "review",
                "--change-id", "CHG-V031-RUNTIME",
                "--decision", "approve",
                "--reviewer", "independent-reviewer",
                "--rationale", "reviewed by real runtime",
                "--runtime", "hermes",
                "--health-check", "pass",
                "--invocation-status", "success",
                "--fallback-reviewer", "none",
                "--review-artifact-ref", "docs/reports/hermes-review.md",
            )
            review = load_yaml(change_dir / "review.yaml")
            self.assertEqual(review["runtime_evidence"]["runtime"], "hermes")
            self.assertEqual(review["runtime_evidence"]["review_artifact_ref"], "docs/reports/hermes-review.md")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-V031-SCOPE", "--title", "Scope defaults"])
                main(["--root", str(root), "change", "prepare", "CHG-V031-SCOPE", "--goal", "default exclusions"])
            contract = load_yaml(root / ".governance/changes/CHG-V031-SCOPE/contract.yaml")
            for expected in [".git/**", ".omx/**", ".venv/**", "node_modules/**", "dist/**", ".release/**", ".governance/archive/**", ".governance/runtime/**"]:
                self.assertIn(expected, contract["scope_out"])

    def test_version_reports_current_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self._run_cli(root, "version")
            self.assertIn("open-cowork 0.3.4", output)

    def _prepare_change(self, root: Path, change_id: str) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--root", str(root), "init"])
            main(["--root", str(root), "change", "create", change_id, "--title", "Govern status commands"])
            main(["--root", str(root), "participants", "setup", "--profile", "personal", "--change-id", change_id])
            main([
                "--root", str(root),
                "intent", "capture",
                "--change-id", change_id,
                "--project-intent", "Govern status commands",
                "--requirement", "Expose status commands",
                "--confirmed-by", "human-sponsor",
            ])
            main(["--root", str(root), "change", "prepare", change_id, "--goal", "Govern status commands"])

    def _run_cli(self, root: Path, *args: str) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, 0, output)
        return output

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {"step6_entry_ready": True, "missing_items": []},
            "roles": {"executor": "executor-agent", "verifier": "verifier-agent", "reviewer": "independent-reviewer"},
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "title": change_id,
            "objective": "v0.3.1 behavior",
            "scope_in": ["src/**", "tests/**", f".governance/changes/{change_id}/evidence/**"],
            "scope_out": [".governance/archive/**", ".governance/runtime/**"],
            "allowed_actions": ["edit_files", "run_commands", "write_evidence"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["src/**", "tests/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["v031"]},
            "evidence_expectations": {"required": ["command_output", "test_output", "changed_files_manifest"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "1": {"owner": "human-sponsor", "gate": "review-required", "human_gate": True},
                "2": {"owner": "analyst-agent", "gate": "approval-required", "human_gate": True},
                "3": {"owner": "architect-agent", "gate": "review-required", "human_gate": True},
                "4": {"owner": "orchestrator-agent", "gate": "review-required", "human_gate": False},
                "5": {"owner": "human-sponsor", "gate": "approval-required", "human_gate": True},
                "6": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False},
                "7": {"owner": "verifier-agent", "gate": "review-required", "human_gate": False},
                "8": {"owner": "independent-reviewer", "reviewer": "independent-reviewer", "gate": "approval-required", "human_gate": True},
                "9": {"owner": "maintainer-agent", "gate": "approval-required", "human_gate": True},
            },
        })
        (change_dir / "tasks.md").write_text("# Tasks\n\nDeliver v0.3.1 behavior.\n", encoding="utf-8")
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
            "residual_followups": [],
        })


if __name__ == "__main__":
    unittest.main()
