from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.continuity import (
    accept_owner_transfer_continuity,
    materialize_continuity_launch_input,
    materialize_handoff_package,
    materialize_round_entry_input_summary,
    prepare_owner_transfer_continuity,
    resolve_continuity_launch_input,
    resolve_handoff_package,
    resolve_round_entry_input_summary,
)
from governance.index import ensure_governance_index, set_current_change, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class ContinuityTests(unittest.TestCase):
    def test_prepare_owner_transfer_continuity_materializes_transfer_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-OT-1"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "owner transfer prepare",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent-a",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "prepare owner transfer continuity",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["OwnerTransferContinuitySchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent-a", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nPrepare owner transfer continuity.\n", encoding="utf-8")

            output_path = Path(prepare_owner_transfer_continuity(
                root,
                change_id=change_id,
                target_role="reviewer",
                outgoing_owner="reviewer-agent-a",
                incoming_owner="reviewer-agent-b",
                reason="session handoff",
                initiated_by="maintainer-agent",
            ))
            payload = load_yaml(output_path)

            self.assertEqual(payload["schema"], "owner-transfer-continuity/v1")
            self.assertEqual(payload["acceptance"]["status"], "pending")
            self.assertEqual(payload["transfer_context"]["incoming_owner"], "reviewer-agent-b")
            self.assertTrue((root / f".governance/changes/{change_id}/handoff-package.yaml").exists())

    def test_accept_owner_transfer_continuity_updates_acceptance_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-OT-2"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "owner-transfer-continuity.yaml", {
                "schema": "owner-transfer-continuity/v1",
                "change_id": change_id,
                "acceptance": {
                    "status": "pending",
                    "accepted_by": None,
                    "accepted_at": None,
                    "note": "",
                },
            })

            payload = accept_owner_transfer_continuity(
                root,
                change_id=change_id,
                accepted_by="reviewer-agent-b",
                note="accept handoff",
            )

            self.assertEqual(payload["acceptance"]["status"], "accepted")
            self.assertEqual(payload["acceptance"]["accepted_by"], "reviewer-agent-b")
            self.assertEqual(payload["acceptance"]["note"], "accept handoff")
            persisted = load_yaml(change_dir / "owner-transfer-continuity.yaml")
            self.assertEqual(persisted["acceptance"]["status"], "accepted")

    def test_accept_owner_transfer_continuity_rejects_non_pending_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-OT-3"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "owner-transfer-continuity.yaml", {
                "schema": "owner-transfer-continuity/v1",
                "change_id": change_id,
                "acceptance": {
                    "status": "accepted",
                    "accepted_by": "reviewer-agent-b",
                    "accepted_at": "2026-04-24T00:00:00Z",
                    "note": "",
                },
            })

            with self.assertRaises(ValueError):
                accept_owner_transfer_continuity(
                    root,
                    change_id=change_id,
                    accepted_by="reviewer-agent-b",
                    note="duplicate accept",
                )

    def test_materialize_handoff_package_without_predecessor_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HO-1"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "handoff package test",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "handoff package generation",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HandoffPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nGenerate handoff package.\n", encoding="utf-8")

            output_path = Path(materialize_handoff_package(root, change_id))
            payload = load_yaml(output_path)

            self.assertEqual(payload["schema"], "handoff-package/v1")
            self.assertEqual(payload["change_id"], change_id)
            self.assertEqual(payload["summary"]["current_status"], "step6-executed-pre-step7")
            self.assertNotIn("carry_forward", payload)

    def test_handoff_package_materializes_runtime_status_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HO-2"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "handoff package runtime materialization",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "materialize runtime status before handoff",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["RuntimeStatusSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nGenerate handoff package.\n", encoding="utf-8")

            output_path = Path(materialize_handoff_package(root, change_id))
            payload = load_yaml(output_path)

            self.assertTrue((root / ".governance/runtime/status/change-status.yaml").exists())
            self.assertEqual(payload["refs"]["runtime_change_status"], ".governance/runtime/status/change-status.yaml")

    def test_handoff_package_uses_optional_refs_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HO-3"
            predecessor_change = "CHG-HO-2"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
                "predecessor_change": predecessor_change,
            })
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "handoff optional refs",
                "status": "step7-verified",
                "current_step": 7,
                "predecessor_change": predecessor_change,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "handoff optional refs",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HandoffPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nGenerate optional handoff refs.\n", encoding="utf-8")
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "reviewers": [{"role": "reviewer", "id": "reviewer-agent"}],
                "decision": {"status": "approve", "rationale": "handoff ready"},
                "conditions": {"must_before_next_step": [], "followups": []},
                "trace": {"evidence_refs": [], "verify_refs": ["verify.yaml"]},
            })
            write_yaml(change_dir / "continuity-launch-input.yaml", {"schema": "continuity-launch-input/v1"})
            write_yaml(change_dir / "ROUND_ENTRY_INPUT_SUMMARY.yaml", {"schema": "round-entry-input-summary/v1"})

            payload = resolve_handoff_package(root, change_id)

            self.assertIn("carry_forward", payload)
            self.assertEqual(payload["carry_forward"]["predecessor_change"], predecessor_change)
            self.assertIn(".governance/changes/CHG-HO-3/continuity-launch-input.yaml", payload["carry_forward"]["carry_forward_refs"])
            self.assertIn("verify", payload["refs"])
            self.assertIn("review", payload["refs"])

    def test_handoff_package_omits_carry_forward_when_predecessor_exists_but_refs_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HO-4"
            predecessor_change = "CHG-HO-3"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
                "predecessor_change": predecessor_change,
            })
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "handoff missing carry-forward refs",
                "status": "step7-verified",
                "current_step": 7,
                "predecessor_change": predecessor_change,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "omit carry forward without continuity refs",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HandoffPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDo not emit empty carry forward.\n", encoding="utf-8")

            payload = resolve_handoff_package(root, change_id)

            self.assertNotIn("carry_forward", payload)

    def test_handoff_package_rebuilds_runtime_status_when_existing_snapshot_belongs_to_another_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            active_change = "CHG-ACTIVE"
            target_change = "CHG-TARGET"
            target_dir = root / f".governance/changes/{target_change}"
            target_dir.mkdir(parents=True, exist_ok=True)

            set_current_change(root, {
                "change_id": target_change,
                "path": f".governance/changes/{target_change}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            upsert_change_entry(root, {
                "change_id": target_change,
                "path": f".governance/changes/{target_change}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            write_yaml(target_dir / "manifest.yaml", {
                "change_id": target_change,
                "title": "handoff runtime snapshot mismatch",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(target_dir / "contract.yaml", {
                "objective": "refresh stale runtime snapshot",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HandoffPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(target_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (target_dir / "tasks.md").write_text("# Tasks\n\nRefresh stale runtime snapshot.\n", encoding="utf-8")

            runtime_status_dir = root / ".governance/runtime/status"
            runtime_status_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(runtime_status_dir / "change-status.yaml", {
                "schema": "runtime-change-status/v1",
                "change_id": active_change,
                "phase": "Phase 3 / 执行与验证",
                "current_step": 7,
                "current_status": "step7-verified",
                "overall_progress": {"completed_steps": [1, 2, 3, 4, 5, 6, 7], "remaining_steps": [8, 9]},
                "gate_posture": {
                    "waiting_on": "Step 8 / Review and decide",
                    "next_decision": "Step 8 / Review and decide",
                    "human_intervention_required": True,
                },
                "current_owner": "wrong-owner",
                "maintenance_status": "step7-verified",
                "refs": {},
                "generated_at": "2026-04-24T00:00:00Z",
                "active_change_matches_current": False,
            })
            write_yaml(runtime_status_dir / "steps-status.yaml", {
                "schema": "runtime-steps-status/v1",
                "change_id": active_change,
                "phase": "Phase 3 / 执行与验证",
                "current_step": 7,
                "next_step": 8,
                "completed_steps": [1, 2, 3, 4, 5, 6, 7],
                "blocked_steps": [],
                "steps": [],
                "generated_at": "2026-04-24T00:00:00Z",
            })
            write_yaml(runtime_status_dir / "participants-status.yaml", {
                "schema": "runtime-participants-status/v1",
                "change_id": active_change,
                "participants": [],
                "generated_at": "2026-04-24T00:00:00Z",
            })

            payload = resolve_handoff_package(root, target_change)

            self.assertEqual(payload["change_id"], target_change)
            self.assertEqual(payload["summary"]["current_status"], "step6-executed-pre-step7")
            refreshed_change_status = load_yaml(runtime_status_dir / "change-status.yaml")
            self.assertEqual(refreshed_change_status["change_id"], target_change)

    def test_handoff_package_fails_without_active_change_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with self.assertRaises(ValueError):
                resolve_handoff_package(root)

    def test_materialize_continuity_launch_input_from_archived_predecessor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-2"
            predecessor_change = "CHG-1"

            set_current_change(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
            })
            upsert_change_entry(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
                "predecessor_change": predecessor_change,
                "validation_focus": "continuity-over-breadth",
            })

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
            (root / f".governance/changes/{current_change}").mkdir(parents=True, exist_ok=True)

            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve_with_conditions"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "lifecycle": {"step9": {"status": "completed"}},
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "archive_executed": True,
                "archived_at": "2026-04-20T00:00:00Z",
            })

            output_path = Path(materialize_continuity_launch_input(root, current_change))
            payload = load_yaml(output_path)

            self.assertEqual(payload["change_id"], current_change)
            self.assertEqual(payload["current_change"]["predecessor_change"], predecessor_change)
            self.assertEqual(payload["predecessor_review_baseline"]["decision_status"], "approve_with_conditions")
            self.assertTrue(payload["predecessor_archive_baseline"]["archive_executed"])
            self.assertTrue(payload["launch_readiness"]["review_to_archive_to_launch_chain_explicit"])
            self.assertEqual(payload["decision_summary"]["current_phase"], "Phase 2 / 方案与准备")
            self.assertEqual(payload["decision_summary"]["next_decision"], "Step 5 / Approve the start")
            self.assertIn("validation_focus", payload["decision_summary"]["current_summary"])
            self.assertTrue(any("manifest.yaml" in item for item in payload["decision_summary"]["next_input_suggestion"]))

    def test_materialize_round_entry_input_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-2"
            predecessor_change = "CHG-1"

            set_current_change(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
            })
            upsert_change_entry(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
                "predecessor_change": predecessor_change,
                "validation_focus": "continuity-over-breadth",
            })

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
            change_dir = root / f".governance/changes/{current_change}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            change_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve_with_conditions"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "lifecycle": {"step9": {"status": "completed"}},
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "archive_executed": True,
                "archived_at": "2026-04-20T00:00:00Z",
            })
            for name in ["manifest.yaml", "contract.yaml", "requirements.md", "tasks.md", "bindings.yaml", "intent.md", "design.md"]:
                path = change_dir / name
                if name.endswith(".yaml"):
                    write_yaml(path, {"placeholder": name})
                else:
                    path.write_text(name, encoding="utf-8")

            output_path = Path(materialize_round_entry_input_summary(root, current_change))
            payload = load_yaml(output_path)

            self.assertEqual(payload["change_id"], current_change)
            self.assertEqual(payload["purpose"], "smaller-round-entry-reading-surface")
            self.assertEqual(payload["operator_start_pack"][0]["path"], f".governance/changes/{current_change}/manifest.yaml")
            self.assertTrue(payload["carry_forward_baseline"])

    def test_continuity_resolves_with_nested_current_change_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-2"
            predecessor_change = "CHG-1"
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "current_change": {
                    "change_id": current_change,
                    "status": "step5-prepared",
                    "current_step": 5,
                },
            })
            upsert_change_entry(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
                "predecessor_change": predecessor_change,
                "validation_focus": "continuity-over-breadth",
            })
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
            change_dir = root / f".governance/changes/{current_change}"
            archive_dir = root / f".governance/archive/{predecessor_change}"
            change_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "id": current_change,
                "status": "step5-prepared",
                "current_step": 5,
                "predecessor_change": predecessor_change,
            })
            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve_with_conditions"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {"lifecycle": {"step9": {"status": "completed"}}})
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True, "archived_at": "2026-04-20T00:00:00Z"})
            payload = resolve_continuity_launch_input(root)

            self.assertEqual(payload["change_id"], current_change)
            self.assertEqual(payload["current_change"]["predecessor_change"], predecessor_change)
            self.assertEqual(payload["predecessor_review_baseline"]["decision_status"], "approve_with_conditions")
            self.assertEqual(payload["maintenance_baseline"]["last_archived_change"], predecessor_change)
            self.assertTrue(payload["predecessor_archive_baseline"]["archive_executed"])

    def test_round_entry_summary_contains_carry_forward_review_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-2"
            predecessor_change = "CHG-1"
            set_current_change(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
            })
            upsert_change_entry(root, {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
                "predecessor_change": predecessor_change,
            })
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
            change_dir = root / f".governance/changes/{current_change}"
            archive_dir = root / f".governance/archive/{predecessor_change}"
            change_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.mkdir(parents=True, exist_ok=True)
            for name in ["manifest.yaml", "contract.yaml", "requirements.md", "tasks.md", "bindings.yaml", "intent.md", "design.md"]:
                path = change_dir / name
                if name.endswith(".yaml"):
                    write_yaml(path, {"placeholder": name})
                else:
                    path.write_text(name, encoding="utf-8")
            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve_with_conditions"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {"lifecycle": {"step9": {"status": "completed"}}})
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True, "archived_at": "2026-04-20T00:00:00Z"})

            payload = resolve_round_entry_input_summary(root, current_change)
            self.assertEqual(payload["change_id"], current_change)
            self.assertEqual(payload["operator_start_pack"][0]["path"], f".governance/changes/{current_change}/manifest.yaml")
            self.assertTrue(any(item["path"].endswith("review.yaml") for item in payload["carry_forward_baseline"]))


if __name__ == "__main__":
    unittest.main()
