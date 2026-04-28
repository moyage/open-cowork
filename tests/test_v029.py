from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.simple_yaml import load_yaml


class V029ReviewArchiveGateTests(unittest.TestCase):
    def test_prepare_handoff_mentions_step5_approval_and_step_report_text_is_human_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-HANDOFF", "--title", "Handoff"])

            prepare_stdout = io.StringIO()
            with contextlib.redirect_stdout(prepare_stdout):
                prepare_exit = main([
                    "--root", str(root), "change", "prepare", "CHG-HANDOFF",
                    "--goal", "Show complete human gate handoff",
                ])
            self.assertEqual(prepare_exit, 0)
            self.assertIn("Step 5 approval is required before Step 6 execution", prepare_stdout.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "intent", "confirm", "--change-id", "CHG-HANDOFF", "--confirmed-by", "human-sponsor"])

            report_stdout = io.StringIO()
            with contextlib.redirect_stdout(report_stdout):
                report_exit = main(["--root", str(root), "step", "report", "--change-id", "CHG-HANDOFF", "--step", "5"])
            self.assertEqual(report_exit, 0)
            output = report_stdout.getvalue()
            self.assertIn("Inputs:", output)
            self.assertIn("Outputs:", output)
            self.assertIn("Done criteria:", output)
            self.assertIn("Participant responsibilities:", output)

    def test_reviewer_mismatch_is_blocked_unless_explicitly_allowed_with_audit_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_verified_change(root, "CHG-REVIEWER")

            blocked = io.StringIO()
            with contextlib.redirect_stdout(blocked):
                blocked_exit = main([
                    "--root", str(root), "review",
                    "--change-id", "CHG-REVIEWER",
                    "--decision", "approve",
                    "--reviewer", "wrong-reviewer",
                    "--rationale", "Wrong actor should not approve",
                ])
            self.assertEqual(blocked_exit, 1)
            self.assertIn("reviewer does not match Step 8 binding", blocked.getvalue())
            review_payload = load_yaml(root / ".governance/changes/CHG-REVIEWER/review.yaml")
            self.assertEqual(review_payload, {})

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-REVIEWER",
                    "--step", "8",
                    "--approved-by", "human-sponsor",
                    "--recorded-by", "orchestrator-agent",
                    "--evidence-ref", "meeting-notes/review-approval.md",
                ])

            allowed = io.StringIO()
            with contextlib.redirect_stdout(allowed):
                allowed_exit = main([
                    "--root", str(root), "review",
                    "--change-id", "CHG-REVIEWER",
                    "--decision", "approve",
                    "--reviewer", "wrong-reviewer",
                    "--rationale", "Allowed with explicit audit",
                    "--allow-reviewer-mismatch",
                    "--bypass-reason", "human accepted reviewer substitution",
                    "--bypass-recorded-by", "human-sponsor",
                    "--bypass-evidence-ref", "meeting-notes/reviewer-substitution.md",
                ])
            self.assertEqual(allowed_exit, 0)
            gates = load_yaml(root / ".governance/changes/CHG-REVIEWER/human-gates.yaml")
            self.assertEqual(gates["bypasses"][0]["step"], 8)
            self.assertEqual(gates["bypasses"][0]["reason"], "human accepted reviewer substitution")
            self.assertIn("reviewer mismatch allowed", allowed.getvalue())

    def test_step8_and_step9_approvals_are_required_and_archive_finalizes_step9_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_verified_change(root, "CHG-GATES")

            blocked_mismatch_bypass = io.StringIO()
            with contextlib.redirect_stdout(blocked_mismatch_bypass):
                blocked_mismatch_exit = main([
                    "--root", str(root), "review",
                    "--change-id", "CHG-GATES",
                    "--decision", "approve",
                    "--reviewer", "wrong-reviewer",
                    "--rationale", "Allowed mismatch still needs Step 8 approval first",
                    "--allow-reviewer-mismatch",
                ])
            self.assertEqual(blocked_mismatch_exit, 1)
            self.assertIn("reviewer mismatch bypass requires", blocked_mismatch_bypass.getvalue())
            gates = load_yaml(root / ".governance/changes/CHG-GATES/human-gates.yaml")
            self.assertEqual(gates.get("bypasses", []), [])

            review_stdout = io.StringIO()
            with contextlib.redirect_stdout(review_stdout):
                review_exit = main([
                    "--root", str(root), "review",
                    "--change-id", "CHG-GATES",
                    "--decision", "approve",
                    "--reviewer", "review-agent",
                    "--rationale", "Reviewer decision arrives before human acceptance",
                ])
            self.assertEqual(review_exit, 0)
            self.assertIn("Review recorded", review_stdout.getvalue())

            missing_step8 = io.StringIO()
            with contextlib.redirect_stdout(missing_step8):
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-GATES"])
            self.assertEqual(archive_exit, 1)
            self.assertIn("Step 8 human gate approval is required", missing_step8.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-GATES",
                    "--step", "8",
                    "--approved-by", "human-sponsor",
                    "--recorded-by", "orchestrator-agent",
                    "--evidence-ref", "meeting-notes/step8.md",
                ])

            missing_step9 = io.StringIO()
            with contextlib.redirect_stdout(missing_step9):
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-GATES"])
            self.assertEqual(archive_exit, 1)
            self.assertIn("Step 9 human gate approval is required", missing_step9.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-GATES",
                    "--step", "9",
                    "--approved-by", "human-sponsor",
                    "--recorded-by", "orchestrator-agent",
                    "--evidence-ref", "meeting-notes/step9.md",
                ])
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-GATES"])
            self.assertEqual(archive_exit, 0)
            archive_dir = root / ".governance/archive/CHG-GATES"
            step9 = load_yaml(archive_dir / "step-reports/step-9.yaml")
            receipt = load_yaml(archive_dir / "archive-receipt.yaml")
            gates = load_yaml(archive_dir / "human-gates.yaml")
            final_consistency = load_yaml(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml")
            self.assertEqual(step9["status"], "archived")
            self.assertEqual(step9["blockers"], [])
            self.assertEqual(receipt["traceability"]["final_step_report"], ".governance/archive/CHG-GATES/step-reports/step-9.yaml")
            self.assertEqual(gates["approvals"][8]["recorded_by"], "orchestrator-agent")
            self.assertEqual(gates["approvals"][9]["evidence_ref"], "meeting-notes/step9.md")
            self.assertEqual(final_consistency["human_gate_summary"][8]["status"], "approved")
            self.assertEqual(final_consistency["human_gate_summary"][9]["evidence_ref"], "meeting-notes/step9.md")

    def test_status_outputs_9_step_progress_table_with_gate_and_approval_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._prepare_verified_change(root, "CHG-STATUS")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status_exit = main(["--root", str(root), "status"])
            self.assertEqual(status_exit, 0)
            output = stdout.getvalue()
            self.assertIn("9-step progress", output)
            self.assertIn("Step 5", output)
            self.assertIn("approval=approved", output)
            self.assertIn("Step 8", output)
            self.assertIn("report=.governance/changes/CHG-STATUS/step-reports/step-8.md", output)
            self.assertIn("Step 9", output)
            self.assertIn("approval=pending", output)

    def _prepare_verified_change(self, root: Path, change_id: str) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--root", str(root), "init"])
            main(["--root", str(root), "change", "create", change_id, "--title", change_id])
            main([
                "--root", str(root), "change", "prepare", change_id,
                "--goal", "Exercise v0.2.9 gate behavior",
                "--scope-in", "src/**",
                "--scope-in", "tests/**",
            ])
            main([
                "--root", str(root), "participants", "setup",
                "--change-id", change_id,
                "--participant", "review-agent:reviewer",
                "--step-reviewer", "8=review-agent",
            ])
            main([
                "--root", str(root), "intent", "capture",
                "--change-id", change_id,
                "--project-intent", "Verified change for gate tests",
                "--scope-in", "src/**",
                "--scope-in", "tests/**",
            ])
            main(["--root", str(root), "intent", "confirm", "--change-id", change_id, "--confirmed-by", "human-sponsor"])
            for step in (1, 2, 3, 5):
                main(["--root", str(root), "step", "approve", "--change-id", change_id, "--step", str(step), "--approved-by", "human-sponsor"])
            main([
                "--root", str(root), "run",
                "--change-id", change_id,
                "--command-output", "ok",
                "--test-output", "tests passed",
                "--modified", "src/governance/review.py",
            ])
            main(["--root", str(root), "verify", "--change-id", change_id])
