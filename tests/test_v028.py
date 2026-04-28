from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.simple_yaml import load_yaml, write_yaml


class V028HumanGatesTests(unittest.TestCase):
    def test_participants_setup_maps_custom_agents_to_steps_and_prepare_preserves_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-MAP", "--title", "Mapping"])
                main([
                    "--root", str(root), "change", "prepare", "CHG-MAP",
                    "--goal", "Prepare before custom mapping",
                ])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root), "participants", "setup",
                    "--profile", "personal",
                    "--participant", "coding-agent:executor",
                    "--participant", "verification-agent:verifier",
                    "--participant", "review-agent:reviewer",
                    "--participant", "observer-agent:observer",
                    "--step-owner", "6=coding-agent",
                    "--step-owner", "7=verification-agent",
                    "--step-reviewer", "8=review-agent",
                    "--change-id", "CHG-MAP",
                ])

            self.assertEqual(exit_code, 0)
            self.assertIn("unassigned participant: observer-agent", stdout.getvalue())
            bindings = load_yaml(root / ".governance/changes/CHG-MAP/bindings.yaml")
            self.assertEqual(bindings["steps"][6]["owner"], "coding-agent")
            self.assertEqual(bindings["steps"][7]["owner"], "verification-agent")
            self.assertEqual(bindings["steps"][8]["reviewer"], "review-agent")

            with contextlib.redirect_stdout(io.StringIO()):
                prepare_exit = main([
                    "--root", str(root), "change", "prepare", "CHG-MAP",
                    "--goal", "Prepare again without losing mapped participants",
                ])
            self.assertEqual(prepare_exit, 0)
            preserved = load_yaml(root / ".governance/changes/CHG-MAP/bindings.yaml")
            self.assertEqual(preserved["steps"][6]["owner"], "coding-agent")
            self.assertEqual(preserved["steps"][7]["owner"], "verification-agent")
            self.assertEqual(preserved["steps"][8]["reviewer"], "review-agent")

    def test_step_approval_is_required_before_run_when_step5_has_human_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-GATE", "--title", "Gate"])
                main([
                    "--root", str(root), "change", "prepare", "CHG-GATE",
                    "--goal", "Require human approval before execution",
                    "--scope-in", "src/**",
                    "--scope-in", "tests/**",
                ])
                main(["--root", str(root), "participants", "setup", "--change-id", "CHG-GATE"])

            blocked = io.StringIO()
            with contextlib.redirect_stdout(blocked):
                blocked_exit = main([
                    "--root", str(root), "run",
                    "--change-id", "CHG-GATE",
                    "--command-output", "ok",
                    "--test-output", "tests passed",
                    "--modified", "src/governance/run.py",
                ])
            self.assertEqual(blocked_exit, 1)
            self.assertIn("cannot run from step 1", blocked.getvalue())

            approved = io.StringIO()
            with contextlib.redirect_stdout(approved):
                for step in (1, 2, 3):
                    main([
                        "--root", str(root), "step", "approve",
                        "--change-id", "CHG-GATE",
                        "--step", str(step),
                        "--approved-by", "human-sponsor",
                    ])
                approve_exit = main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-GATE",
                    "--step", "5",
                    "--approved-by", "human-sponsor",
                    "--note", "Execution approved",
                ])
            self.assertEqual(approve_exit, 0)
            self.assertIn("Step 5 approved", approved.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                run_exit = main([
                    "--root", str(root), "run",
                    "--change-id", "CHG-GATE",
                    "--command-output", "ok",
                    "--test-output", "tests passed",
                    "--modified", "src/governance/run.py",
                ])
            self.assertEqual(run_exit, 0)
            gates = load_yaml(root / ".governance/changes/CHG-GATE/human-gates.yaml")
            self.assertEqual(gates["approvals"][5]["approved_by"], "human-sponsor")

    def test_command_flow_generates_step_reports_and_unconfirmed_intent_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-REPORTS", "--title", "Reports"])
                main([
                    "--root", str(root), "change", "prepare", "CHG-REPORTS",
                    "--goal", "Generate default reports",
                ])

            change_dir = root / ".governance/changes/CHG-REPORTS"
            self.assertTrue((change_dir / "step-reports/step-1.yaml").exists())
            for step in (2, 3, 4, 5):
                self.assertFalse((change_dir / f"step-reports/step-{step}.yaml").exists())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                capture_exit = main([
                    "--root", str(root), "intent", "capture",
                    "--change-id", "CHG-REPORTS",
                    "--project-intent", "Captured but not yet confirmed",
                ])
            self.assertEqual(capture_exit, 0)
            self.assertIn("Step 1", stdout.getvalue())
            self.assertIn("confirm Step 1 before generating future step reports", stdout.getvalue())
            self.assertTrue((change_dir / "step-reports/step-1.yaml").exists())
            self.assertFalse((change_dir / "step-reports/step-2.yaml").exists())
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertFalse(manifest["readiness"]["step6_entry_ready"])

            with contextlib.redirect_stdout(io.StringIO()):
                confirm_exit = main([
                    "--root", str(root), "intent", "confirm",
                    "--change-id", "CHG-REPORTS",
                    "--confirmed-by", "human-sponsor",
                ])
            self.assertEqual(confirm_exit, 0)
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertTrue(manifest["readiness"]["step6_entry_ready"])

    def test_step_report_on_draft_contract_returns_human_readable_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-DRAFT", "--title", "Draft"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root), "step", "report",
                    "--change-id", "CHG-DRAFT",
                    "--step", "5",
                ])

            self.assertEqual(exit_code, 1)
            self.assertIn("Step report failed", stdout.getvalue())
            self.assertIn("run 'ocw change prepare'", stdout.getvalue())

    def test_adopt_and_contract_validate_surface_human_control_and_scope_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])

            adopt_stdout = io.StringIO()
            with contextlib.redirect_stdout(adopt_stdout):
                adopt_exit = main([
                    "--root", str(root), "adopt",
                    "--target", str(root),
                    "--goal", "Dogfood v0.2.8 human gates",
                    "--dry-run",
                ])
            self.assertEqual(adopt_exit, 0)
            self.assertIn("Human control baseline next actions", adopt_stdout.getvalue())
            self.assertIn("step approve", adopt_stdout.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "change", "create", "CHG-DRIFT", "--title", "Drift"])
                main([
                    "--root", str(root), "change", "prepare", "CHG-DRIFT",
                    "--goal", "Detect scope drift",
                    "--scope-in", "src/**",
                ])
                main([
                    "--root", str(root), "intent", "capture",
                    "--change-id", "CHG-DRIFT",
                    "--project-intent", "Touch docs only",
                    "--scope-in", "docs/**",
                ])
                main([
                    "--root", str(root), "intent", "confirm",
                    "--change-id", "CHG-DRIFT",
                    "--confirmed-by", "human-sponsor",
                ])

            validate_stdout = io.StringIO()
            with contextlib.redirect_stdout(validate_stdout):
                validate_exit = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-DRIFT"])
            self.assertEqual(validate_exit, 1)
            self.assertIn("intent scope differs from contract scope", validate_stdout.getvalue())

    def test_review_warns_on_reviewer_mismatch_and_archive_writes_final_state_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-ARCHIVE", "--title", "Archive"])
                main([
                    "--root", str(root), "change", "prepare", "CHG-ARCHIVE",
                    "--goal", "Archive with final state audit",
                ])
                main(["--root", str(root), "participants", "setup", "--change-id", "CHG-ARCHIVE"])
                for step in (1, 2, 3, 5):
                    main([
                        "--root", str(root), "step", "approve",
                        "--change-id", "CHG-ARCHIVE", "--step", str(step), "--approved-by", "human-sponsor",
                    ])
                main([
                    "--root", str(root), "run",
                    "--change-id", "CHG-ARCHIVE",
                    "--command-output", "ok",
                    "--test-output", "tests passed",
                    "--modified", "src/governance/archive.py",
                ])
                main(["--root", str(root), "verify", "--change-id", "CHG-ARCHIVE"])
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-ARCHIVE", "--step", "8", "--approved-by", "human-sponsor",
                ])

            review_stdout = io.StringIO()
            with contextlib.redirect_stdout(review_stdout):
                review_exit = main([
                    "--root", str(root), "review",
                    "--change-id", "CHG-ARCHIVE",
                    "--decision", "approve",
                    "--reviewer", "review-agent",
                    "--rationale", "Approved with external reviewer",
                    "--allow-reviewer-mismatch",
                    "--bypass-reason", "human accepted reviewer substitution",
                    "--bypass-recorded-by", "human-sponsor",
                    "--bypass-evidence-ref", "meeting-notes/reviewer-substitution.md",
                ])
            self.assertEqual(review_exit, 0)
            self.assertIn("reviewer does not match Step 8 binding", review_stdout.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-ARCHIVE", "--step", "8", "--approved-by", "human-sponsor",
                ])
                main([
                    "--root", str(root), "step", "approve",
                    "--change-id", "CHG-ARCHIVE", "--step", "9", "--approved-by", "human-sponsor",
                ])
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-ARCHIVE"])
            self.assertEqual(archive_exit, 0)
            archive_dir = root / ".governance/archive/CHG-ARCHIVE"
            final_snapshot = load_yaml(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml")
            receipt = load_yaml(archive_dir / "archive-receipt.yaml")
            self.assertEqual(final_snapshot["lifecycle_at_generation"], "archived")
            self.assertEqual(receipt["traceability"]["final_state_consistency"], ".governance/archive/CHG-ARCHIVE/FINAL_STATE_CONSISTENCY_CHECK.yaml")
