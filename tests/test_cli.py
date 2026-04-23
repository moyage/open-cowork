from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index, read_changes_index, read_current_change, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class CliTests(unittest.TestCase):
    def test_change_create_sets_active_change_and_index_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-1",
                    "--title",
                    "CLI change package",
                ])

            self.assertEqual(exit_code, 0)
            current_change = read_current_change(root)
            changes_index = read_changes_index(root)
            manifest = load_yaml(root / ".governance/changes/CHG-CLI-1/manifest.yaml")

            self.assertEqual(current_change["current_change_id"], "CHG-CLI-1")
            self.assertEqual(current_change["status"], "drafting")
            self.assertEqual(manifest["title"], "CLI change package")
            self.assertEqual(changes_index["changes"][0]["change_id"], "CHG-CLI-1")
            self.assertIn("Created change package CHG-CLI-1", stdout.getvalue())

    def test_contract_validate_and_run_review_archive_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-2",
                    "--title",
                    "CLI lifecycle",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-2"
            contract_path = change_dir / "contract.yaml"
            write_yaml(contract_path, {
                "objective": "milestone1-stage1-cli-closure",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": ["python3 -m unittest discover -s tests -v"], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            write_yaml(change_dir / "manifest.yaml", manifest)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                validate_exit = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-CLI-2"])
            self.assertEqual(validate_exit, 0)
            self.assertIn("Contract valid", stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                run_exit = main([
                    "--root",
                    str(root),
                    "run",
                    "--change-id",
                    "CHG-CLI-2",
                    "--command",
                    "python3 -m unittest discover -s tests -v",
                    "--command-output",
                    "ok",
                    "--test-output",
                    "tests passed",
                    "--created",
                    "src/governance/runtime_stage1.py",
                    "--modified",
                    "tests/test_cli.py",
                ])
            self.assertEqual(run_exit, 0)
            self.assertTrue((change_dir / "evidence/execution-summary.yaml").exists())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                review_exit = main([
                    "--root",
                    str(root),
                    "review",
                    "--change-id",
                    "CHG-CLI-2",
                    "--decision",
                    "approve",
                    "--reviewer",
                    "reviewer-agent",
                    "--rationale",
                    "Stage 1 minimum chain accepted",
                ])
            self.assertEqual(review_exit, 0)
            review_payload = load_yaml(change_dir / "review.yaml")
            self.assertEqual(review_payload["decision"]["status"], "approve")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-CLI-2"])
            self.assertEqual(archive_exit, 0)

            archive_dir = root / ".governance/archive/CHG-CLI-2"
            self.assertTrue((archive_dir / "manifest.yaml").exists())
            self.assertTrue((archive_dir / "archive-receipt.yaml").exists())
            archive_receipt = load_yaml(archive_dir / "archive-receipt.yaml")
            self.assertTrue(archive_receipt["archive_executed"])

            current_change = read_current_change(root)
            changes_index = read_changes_index(root)
            maintenance = load_yaml(root / ".governance/index/maintenance-status.yaml")
            self.assertEqual(current_change["status"], "idle")
            self.assertIsNone(current_change["current_change_id"])
            self.assertEqual(changes_index["changes"][0]["status"], "archived")
            self.assertEqual(maintenance["last_archived_change"], "CHG-CLI-2")

    def test_status_outputs_human_facing_phase_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-3",
                    "--title",
                    "Human snapshot",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-3"
            write_yaml(change_dir / "contract.yaml", {
                "objective": "surface-project-status-clearly",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HumanStatusSnapshot"],
                "verification": {"commands": ["python3 -m unittest discover -s tests -v"], "checks": ["status snapshot visible"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDeliver a human-readable progress snapshot.\n", encoding="utf-8")
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["status"] = "step6-executed-pre-step7"
            manifest["current_step"] = 6
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            manifest["roles"] = {"executor": "executor-agent", "reviewer": "reviewer-agent", "formal_orchestrator": "pm-agent"}
            manifest["target_validation_objects"] = ["HumanStatusSnapshot"]
            write_yaml(change_dir / "manifest.yaml", manifest)
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step6-executed-pre-step7",
                "current_change_id": "CHG-CLI-3",
                "current_step": 6,
                "current_change": {
                    "change_id": "CHG-CLI-3",
                    "status": "step6-executed-pre-step7",
                    "current_step": 6,
                },
            })
            upsert_change_entry(root, {
                "change_id": "CHG-CLI-3",
                "path": ".governance/changes/CHG-CLI-3",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "title": "Human snapshot",
                "validation_focus": "human-status-surface",
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "status"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("current_phase: Phase 3 / 执行与验证", output)
            self.assertIn("current_owner: executor-agent", output)
            self.assertIn("waiting_on: Step 7 verify outputs and review-ready decision", output)
            self.assertIn("next_decision: Step 8 / Review and decide", output)
            self.assertIn("project_summary: Deliver a human-readable progress snapshot.", output)
            self.assertTrue((change_dir / "STATUS_SNAPSHOT.yaml").exists())

    def test_continuity_commands_materialize_launch_input_and_round_entry_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-CLI-4"
            predecessor_change = "CHG-CLI-3"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    current_change,
                    "--title",
                    "Continuity packet",
                ])

            set_current = {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
            }
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step5-prepared",
                "current_change_id": current_change,
                "current_step": 5,
                "current_change": set_current,
            })
            changes_index = read_changes_index(root)
            changes_index["changes"][0]["predecessor_change"] = predecessor_change
            write_yaml(root / ".governance/index/changes-index.yaml", changes_index)
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "preparing-next-round",
                "current_change_active": True,
                "current_change_id": current_change,
                "last_archived_change": predecessor_change,
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": predecessor_change,
                    "archive_path": f".governance/archive/{predecessor_change}/",
                    "archived_at": "2026-04-20T00:00:00Z",
                    "receipt": f".governance/archive/{predecessor_change}/archive-receipt.yaml",
                }],
            })
            archive_dir = root / f".governance/archive/{predecessor_change}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {"lifecycle": {"step9": {"status": "completed"}}})
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True, "archived_at": "2026-04-20T00:00:00Z"})

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                launch_exit = main(["--root", str(root), "continuity", "launch-input", "--change-id", current_change])
            self.assertEqual(launch_exit, 0)
            self.assertIn("continuity-launch-input.yaml", stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                summary_exit = main(["--root", str(root), "continuity", "round-entry-summary", "--change-id", current_change])
            self.assertEqual(summary_exit, 0)
            self.assertIn("ROUND_ENTRY_INPUT_SUMMARY.yaml", stdout.getvalue())

            self.assertTrue((root / f".governance/changes/{current_change}/continuity-launch-input.yaml").exists())
            self.assertTrue((root / f".governance/changes/{current_change}/ROUND_ENTRY_INPUT_SUMMARY.yaml").exists())


if __name__ == "__main__":
    unittest.main()
