from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class RuntimeStatusTests(unittest.TestCase):
    def test_runtime_status_requires_active_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            active_dir = root / ".governance/changes/CHG-ACTIVE"
            active_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(active_dir / "manifest.yaml", {
                "change_id": "CHG-ACTIVE",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            inactive_dir = root / ".governance/changes/CHG-INACTIVE"
            inactive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(inactive_dir / "manifest.yaml", {
                "change_id": "CHG-INACTIVE",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step7-verified",
                "current_change_id": "CHG-ACTIVE",
                "current_step": 7,
                "current_change": {
                    "change_id": "CHG-ACTIVE",
                    "status": "step7-verified",
                    "current_step": 7,
                },
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "runtime-status", "--change-id", "CHG-INACTIVE"])

            self.assertEqual(exit_code, 1)
            self.assertIn("active change", stdout.getvalue())

    def test_runtime_status_writes_machine_readable_status_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_dir = root / ".governance/changes/CHG-RT-1"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": "CHG-RT-1",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
                "target_validation_objects": ["RuntimeStatusSchema"],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "emit-machine-readable-runtime-status",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["RuntimeStatusSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest discover -s tests -v"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nExpose runtime status for external readers.\n", encoding="utf-8")
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-RT-1",
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step7-verified",
                "current_change_id": "CHG-RT-1",
                "current_step": 7,
                "current_change": {
                    "change_id": "CHG-RT-1",
                    "status": "step7-verified",
                    "current_step": 7,
                },
            })
            upsert_change_entry(root, {
                "change_id": "CHG-RT-1",
                "path": ".governance/changes/CHG-RT-1",
                "status": "step7-verified",
                "current_step": 7,
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "step7-verified",
                "current_change_active": "step7-verified",
                "current_change_id": "CHG-RT-1",
                "last_archived_change": None,
                "last_archive_at": None,
                "residual_followups": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "runtime-status", "--change-id", "CHG-RT-1"])

            self.assertEqual(exit_code, 0)
            runtime_status_dir = root / ".governance/runtime/status"
            change_status = load_yaml(runtime_status_dir / "change-status.yaml")
            steps_status = load_yaml(runtime_status_dir / "steps-status.yaml")
            participants_status = load_yaml(runtime_status_dir / "participants-status.yaml")

            self.assertEqual(change_status["schema"], "runtime-change-status/v1")
            self.assertEqual(change_status["change_id"], "CHG-RT-1")
            self.assertEqual(change_status["current_status"], "step7-verified")
            self.assertEqual(change_status["phase"], "Phase 3 / 执行与验证")
            self.assertEqual(steps_status["schema"], "runtime-steps-status/v1")
            self.assertTrue(any(step["step"] == 7 and step["status"] == "completed" for step in steps_status["steps"]))
            self.assertEqual(participants_status["schema"], "runtime-participants-status/v1")
            self.assertTrue(any(item["role"] == "reviewer" and item["actor_id"] == "reviewer-agent" for item in participants_status["participants"]))
            self.assertIn("Runtime status written", stdout.getvalue())

    def test_timeline_writes_current_month_event_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_dir = root / ".governance/changes/CHG-RT-2"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": "CHG-RT-2",
                "status": "review-approved",
                "current_step": 8,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
                "target_validation_objects": ["RuntimeTimelineSchema"],
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "emit-runtime-timeline",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["RuntimeTimelineSchema"],
                "verification": {"checks": ["timeline-generated"], "commands": ["python3 -m unittest discover -s tests -v"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-RT-2",
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": "CHG-RT-2",
                "reviewers": [{"role": "reviewer", "id": "reviewer-agent"}],
                "decision": {"status": "approve", "rationale": "timeline ready"},
                "conditions": {"must_before_next_step": [], "followups": []},
                "trace": {"evidence_refs": [], "verify_refs": ["verify.yaml"]},
            })
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "review-approved",
                "current_change_id": "CHG-RT-2",
                "current_step": 8,
                "current_change": {
                    "change_id": "CHG-RT-2",
                    "status": "review-approved",
                    "current_step": 8,
                },
            })
            upsert_change_entry(root, {
                "change_id": "CHG-RT-2",
                "path": ".governance/changes/CHG-RT-2",
                "status": "review-approved",
                "current_step": 8,
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "review-approved",
                "current_change_active": "review-approved",
                "current_change_id": "CHG-RT-2",
                "last_archived_change": None,
                "last_archive_at": None,
                "residual_followups": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "timeline", "--change-id", "CHG-RT-2"])

            self.assertEqual(exit_code, 0)
            month_file = root / f".governance/runtime/timeline/events-{datetime.utcnow().strftime('%Y%m')}.yaml"
            payload = load_yaml(month_file)

            self.assertEqual(payload["schema"], "runtime-timeline/v1")
            self.assertTrue(any(event["event_type"] == "change_created" for event in payload["events"]))
            self.assertTrue(any(event["event_type"] == "verify_completed" for event in payload["events"]))
            self.assertTrue(any(event["event_type"] == "review_completed" for event in payload["events"]))
            self.assertTrue(all(event["change_id"] == "CHG-RT-2" for event in payload["events"]))
            self.assertIn("Timeline written", stdout.getvalue())

    def test_timeline_appends_without_overwriting_existing_month_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            month_key = datetime.utcnow().strftime('%Y%m')
            timeline_dir = root / ".governance/runtime/timeline"
            timeline_dir.mkdir(parents=True, exist_ok=True)
            existing_event = {
                "schema": "runtime-event/v1",
                "event_id": "CHG-OLD-change_created",
                "change_id": "CHG-OLD",
                "entity_type": "change",
                "event_type": "change_created",
                "step": 5,
                "from_status": None,
                "to_status": "drafting",
                "actor_id": "orchestrator",
                "timestamp": "2026-04-24T00:00:00+00:00",
                "refs": {"files": [".governance/changes/CHG-OLD/"]},
            }
            write_yaml(timeline_dir / f"events-{month_key}.yaml", {
                "schema": "runtime-timeline/v1",
                "month": month_key,
                "events": [existing_event],
                "generated_at": "2026-04-24T00:00:00+00:00",
            })

            change_dir = root / ".governance/changes/CHG-RT-3"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": "CHG-RT-3",
                "status": "review-approved",
                "current_step": 8,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-RT-3",
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": "CHG-RT-3",
                "reviewers": [{"role": "reviewer", "id": "reviewer-agent"}],
                "decision": {"status": "approve", "rationale": "timeline ready"},
                "conditions": {"must_before_next_step": [], "followups": []},
                "trace": {"evidence_refs": [], "verify_refs": ["verify.yaml"]},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "timeline", "--change-id", "CHG-RT-3"])

            self.assertEqual(exit_code, 0)
            payload = load_yaml(timeline_dir / f"events-{month_key}.yaml")
            self.assertTrue(any(event["change_id"] == "CHG-OLD" for event in payload["events"]))
            self.assertTrue(any(event["change_id"] == "CHG-RT-3" and event["event_type"] == "review_completed" for event in payload["events"]))

    def test_timeline_uses_source_file_timestamps_for_event_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_dir = root / ".governance/changes/CHG-RT-4"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": "CHG-RT-4",
                "status": "review-approved",
                "current_step": 8,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-RT-4",
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            verify_path = change_dir / "verify.yaml"
            fixed_dt = datetime(2026, 4, 24, 11, 12, 13, tzinfo=timezone.utc)
            fixed_ts = fixed_dt.timestamp()
            verify_path.touch()
            import os
            os.utime(verify_path, (fixed_ts, fixed_ts))

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "timeline", "--change-id", "CHG-RT-4"])

            self.assertEqual(exit_code, 0)
            month_file = root / f".governance/runtime/timeline/events-{datetime.utcnow().strftime('%Y%m')}.yaml"
            payload = load_yaml(month_file)
            verify_event = next(event for event in payload["events"] if event["change_id"] == "CHG-RT-4" and event["event_type"] == "verify_completed")
            self.assertTrue(verify_event["timestamp"].startswith("2026-04-24T11:12:13"))


if __name__ == "__main__":
    unittest.main()
