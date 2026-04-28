from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index
from governance.simple_yaml import load_yaml, write_yaml


class V039PreflightGuardTests(unittest.TestCase):
    def test_preflight_blocks_governed_project_without_active_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")

            output = self._run_cli(root, "preflight", "check", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertFalse(payload["can_execute"])
            self.assertEqual(payload["reason"], "no_active_change")
            self.assertIn("create or confirm a change package", payload["required_action"])

    def test_preflight_blocks_before_step5_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-BLOCKED", current_step=5, status="step5-prepared", step5_approved=False)

            output = self._run_cli(root, "preflight", "check", "--change-id", "CHG-V039-BLOCKED", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertFalse(payload["can_execute"])
            self.assertEqual(payload["reason"], "step5_approval_required")
            self.assertIn("Step 5 human gate approval", payload["required_action"])

    def test_preflight_allows_after_step5_approval_and_points_to_authoritative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-READY", current_step=5, status="step5-approved", step5_approved=True)

            output = self._run_cli(root, "preflight", "check", "--change-id", "CHG-V039-READY", "--format", "json")
            payload = json.loads(output)

            self.assertTrue(payload["can_execute"])
            self.assertEqual(payload["reason"], "ready_for_step6")
            self.assertEqual(payload["contract_ref"], ".governance/changes/CHG-V039-READY/contract.yaml")
            self.assertEqual(payload["evidence_ref"], ".governance/changes/CHG-V039-READY/evidence/")

    def test_preflight_checks_paths_against_contract_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-SCOPE", current_step=5, status="step5-approved", step5_approved=True)

            allowed = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                "foundation/components/Button.tsx",
                "--format",
                "json",
            ))
            outside = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                "src/outside.py",
                "--format",
                "json",
                expect=1,
            ))
            scope_out = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                ".governance/archive/CHG-X/file.yaml",
                "--format",
                "json",
                expect=1,
            ))

            self.assertTrue(allowed["can_execute"])
            self.assertEqual(outside["reason"], "scope_violation")
            self.assertEqual(outside["scope_violations"][0]["reason"], "outside_scope_in")
            self.assertEqual(scope_out["scope_violations"][0]["reason"], "matches_scope_out")

    def test_recovery_records_bypassed_flow_without_normal_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-RECOVERY", current_step=5, status="step5-prepared", step5_approved=False)

            self._run_cli(
                root,
                "preflight",
                "recovery",
                "--change-id",
                "CHG-V039-RECOVERY",
                "--reason",
                "Agent implemented before open-cowork preflight",
                "--modified",
                "foundation/components/Button.tsx",
                "--missing",
                "contract",
                "--missing",
                "evidence",
                "--missing",
                "review",
                "--action",
                "backfill change package as recovery only",
                "--recorded-by",
                "orchestrator-agent",
            )

            recovery = load_yaml(root / ".governance/changes/CHG-V039-RECOVERY/recovery/bypass-records.yaml")
            self.assertEqual(recovery["records"][0]["classification"], "flow_bypass_recovery")
            self.assertEqual(recovery["records"][0]["normal_evidence"], False)
            self.assertEqual(recovery["records"][0]["modified_files"], ["foundation/components/Button.tsx"])
            self.assertFalse((root / ".governance/changes/CHG-V039-RECOVERY/evidence/bypass-records.yaml").exists())

    def test_status_and_activate_show_execution_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-STATUS", current_step=5, status="step5-prepared", step5_approved=False)

            status_output = self._run_cli(root, "status")
            activate_output = self._run_cli(root, "activate", "--change-id", "CHG-V039-STATUS")
            resume_output = self._run_cli(root, "resume", "--change-id", "CHG-V039-STATUS")

            self.assertIn("## Execution preflight", status_output)
            self.assertIn("can_modify_project_files: false", status_output)
            self.assertIn("Execution preflight:", activate_output)
            self.assertIn("can_modify_project_files: false", activate_output)
            self.assertIn("Execution preflight:", resume_output)
            self.assertIn("can_modify_project_files: false", resume_output)

    def test_step1_unconfirmed_does_not_materialize_future_step_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V039-STEP1", "--title", "Step 1 boundary")
            self._run_cli(
                root,
                "change",
                "prepare",
                "CHG-V039-STEP1",
                "--goal",
                "Future reports must not exist before Step 1 confirmation",
                "--scope-in",
                "docs/**",
            )

            reports = sorted(path.name for path in (root / ".governance/changes/CHG-V039-STEP1/step-reports").glob("*"))
            self.assertEqual(reports, ["step-1.md", "step-1.yaml"])

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str, step5_approved: bool) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {
                "step6_entry_ready": step5_approved,
                "missing_items": [] if step5_approved else ["step5_approval"],
            },
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "Preflight guard",
            "scope_in": ["foundation/components/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files", "run_commands"],
            "forbidden_actions": ["no_step6_before_step5_ready"],
            "validation_objects": ["foundation/components/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["v039"]},
            "evidence_expectations": {"required": ["test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "5": {"owner": "human-sponsor", "gate": "approval-required", "human_gate": True},
                "6": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False},
            },
        })
        approvals = {}
        if step5_approved:
            approvals[5] = {"status": "approved", "approved_by": "human-sponsor"}
        write_yaml(change_dir / "human-gates.yaml", {"schema": "human-gates/v1", "change_id": change_id, "approvals": approvals})
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {"change_id": change_id, "status": status, "current_step": current_step},
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/active-changes.yaml", {
            "schema": "active-changes/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


class V039TeamOperatingLoopTests(unittest.TestCase):
    def test_participant_discover_register_assign_and_team_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-TEAM", current_step=6, status="step6-in-progress")

            self._run_cli(root, "participant", "discover", "--recorded-by", "codex-agent")
            self._run_cli(
                root,
                "participant",
                "register",
                "--participant-id",
                "remote-reviewer",
                "--type",
                "agent",
                "--domain",
                "team-remote",
                "--entrypoint",
                "declared-invite://remote-reviewer",
                "--capability",
                "review",
                "--default-role",
                "reviewer",
                "--step",
                "8",
                "--remote",
                "--recorded-by",
                "human-sponsor",
            )
            self._run_cli(root, "participant", "assign", "--participant-id", "codex-agent", "--change-id", "CHG-TEAM", "--step", "6", "--role", "executor", "--recorded-by", "human-sponsor")
            self._run_cli(root, "assignment", "set", "--change-id", "CHG-TEAM", "--step", "8", "--role", "reviewer", "--actor", "remote-reviewer", "--recorded-by", "human-sponsor")

            status = self._run_cli(root, "team", "status", "--format", "json")
            payload = json.loads(status)

            participants = load_yaml(root / ".governance/team/participants.yaml")
            assignments = load_yaml(root / ".governance/team/assignments.yaml")
            self.assertIn("discovered_candidates", participants)
            self.assertEqual(participants["participants"][0]["domain"], "team-remote")
            self.assertTrue(participants["participants"][0]["human_confirmed"])
            self.assertEqual(participants["participants"][0]["review_status"], "human-confirmed")
            self.assertEqual(assignments["assignments"][0]["role"], "executor")
            self.assertEqual(assignments["assignments"][1]["actor"], "remote-reviewer")
            self.assertEqual(payload["active_changes"][0]["executor"], "codex-agent")
            self.assertEqual(payload["active_changes"][0]["reviewer"], "remote-reviewer")

    def test_agent_recorded_participant_registration_remains_pending_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-PARTICIPANT", current_step=1, status="step1-ready")

            self._run_cli(
                root,
                "participant",
                "register",
                "--participant-id",
                "agent-registered",
                "--type",
                "agent",
                "--domain",
                "personal-local",
                "--entrypoint",
                "codex",
                "--capability",
                "execute",
                "--default-role",
                "executor",
                "--step",
                "6",
                "--recorded-by",
                "codex-agent",
            )

            participants = load_yaml(root / ".governance/team/participants.yaml")
            item = participants["participants"][0]
            self.assertFalse(item["human_confirmed"])
            self.assertEqual(item["review_status"], "pending-human-review")
            self.assertNotIn("confirmed_by", item)

    def test_assignment_blocks_reviewer_self_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-SELF", current_step=6, status="step6-in-progress")

            self._run_cli(root, "assignment", "set", "--change-id", "CHG-SELF", "--step", "6", "--role", "executor", "--actor", "same-agent", "--recorded-by", "human-sponsor")
            output = self._run_cli(
                root,
                "assignment",
                "set",
                "--change-id",
                "CHG-SELF",
                "--step",
                "8",
                "--role",
                "reviewer",
                "--actor",
                "same-agent",
                "--recorded-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("reviewer cannot review their own execution", output)

    def test_assignment_blocks_reviewer_self_review_from_existing_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-BINDING-SELF", current_step=6, status="step6-in-progress")
            bindings_path = root / ".governance/changes/CHG-BINDING-SELF/bindings.yaml"
            bindings = load_yaml(bindings_path)
            step6 = bindings["steps"].get("6") or bindings["steps"].get(6) or bindings["steps"].get("'6'")
            step6["executor"] = "same-agent"
            step6["owner"] = "same-agent"
            write_yaml(bindings_path, bindings)

            output = self._run_cli(
                root,
                "assignment",
                "set",
                "--change-id",
                "CHG-BINDING-SELF",
                "--step",
                "8",
                "--role",
                "reviewer",
                "--actor",
                "same-agent",
                "--recorded-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("reviewer cannot review their own execution", output)

    def test_blocked_reviewer_queue_digest_carry_forward_and_retrospective(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-OPS", current_step=7, status="step7-verified")

            self._run_cli(root, "blocked", "set", "--change-id", "CHG-OPS", "--reason", "Need review", "--waiting-on", "reviewer", "--next-decision", "Assign reviewer", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "reviewer", "queue", "--change-id", "CHG-OPS", "--reviewer", "independent-reviewer", "--priority", "high", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "carry-forward", "add", "--item-id", "follow-up-1", "--summary", "Improve team digest", "--source-change-id", "CHG-OPS", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "retrospective", "add", "--retrospective-id", "retro-1", "--change-id", "CHG-OPS", "--summary", "Loop worked", "--learning", "Keep gates visible", "--recorded-by", "maintainer-agent")

            digest = json.loads(self._run_cli(root, "team", "digest", "--format", "json"))

            self.assertEqual(digest["blocked"][0]["change_id"], "CHG-OPS")
            self.assertEqual(digest["reviewer_queue"][0]["priority"], "high")
            self.assertEqual(digest["carry_forward"][0]["id"], "follow-up-1")
            self.assertEqual(digest["retrospectives"][0]["id"], "retro-1")
            self.assertTrue((root / ".governance/team/retrospectives/retro-1.md").exists())

    def test_recurring_intent_and_carry_forward_promote_only_create_step1_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-CURRENT", current_step=5, status="step5-prepared")

            self._run_cli(root, "recurring-intent", "add", "--intent-id", "weekly-sync", "--summary", "Weekly governance sync", "--cadence", "weekly", "--recorded-by", "human-sponsor")
            trigger = json.loads(self._run_cli(root, "recurring-intent", "trigger", "--intent-id", "weekly-sync", "--change-id", "CHG-WEEKLY", "--recorded-by", "orchestrator-agent", "--format", "json"))
            self._run_cli(root, "carry-forward", "add", "--item-id", "cf-1", "--summary", "Next loop item", "--source-change-id", "CHG-CURRENT", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "carry-forward", "promote", "--item-id", "cf-1", "--change-id", "CHG-CF", "--recorded-by", "orchestrator-agent")

            weekly_manifest = load_yaml(root / ".governance/changes/CHG-WEEKLY/manifest.yaml")
            cf_manifest = load_yaml(root / ".governance/changes/CHG-CF/manifest.yaml")
            self.assertEqual(trigger["current_step"], 1)
            self.assertEqual(weekly_manifest["current_step"], 1)
            self.assertEqual(weekly_manifest["status"], "awaiting-intent-confirmation")
            self.assertEqual(cf_manifest["current_step"], 1)
            self.assertNotEqual(cf_manifest["status"], "step6-in-progress")

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {"step6_entry_ready": current_step >= 6, "missing_items": []},
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "Team loop",
            "scope_in": ["src/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files"],
            "forbidden_actions": ["self_review"],
            "validation_objects": ["src/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["team loop"]},
            "evidence_expectations": {"required": ["test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "6": {"owner": "executor-agent", "reviewer": "verifier-agent", "human_gate": False},
                "8": {"owner": "independent-reviewer", "reviewer": "independent-reviewer", "human_gate": True},
            }
        })
        write_yaml(change_dir / "verify.yaml", {"status": "pending"})
        write_yaml(change_dir / "review.yaml", {"decision": {"status": "pending"}})
        entry = {"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step, "title": change_id}
        write_yaml(root / ".governance/index/current-change.yaml", {"schema": "current-change/v1", "status": status, "current_change_id": change_id, "current_step": current_step, "current_change": entry})
        write_yaml(root / ".governance/index/changes-index.yaml", {"schema": "changes-index/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/active-changes.yaml", {"schema": "active-changes/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/maintenance-status.yaml", {"schema": "maintenance-status/v1", "status": status, "current_change_active": status, "current_change_id": change_id})

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
