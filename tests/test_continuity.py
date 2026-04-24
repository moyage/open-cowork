from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.continuity import (
    accept_owner_transfer_continuity,
    append_sync_history,
    export_sync_packet,
    list_sync_history_months,
    materialize_increment_package,
    materialize_continuity_launch_input,
    materialize_closeout_packet,
    materialize_handoff_package,
    materialize_round_entry_input_summary,
    prepare_owner_transfer_continuity,
    resolve_continuity_digest,
    read_sync_history,
    read_sync_history_across_months,
    resolve_increment_package,
    resolve_continuity_launch_input,
    resolve_handoff_package,
    resolve_round_entry_input_summary,
)
from governance.index import ensure_governance_index, set_current_change, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class ContinuityTests(unittest.TestCase):
    def test_resolve_continuity_digest_prefers_current_active_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-ACTIVE"
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
                "title": "Digest Active",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest active",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest active.\n", encoding="utf-8")
            handoff_path = Path(materialize_handoff_package(root, change_id))

            payload = resolve_continuity_digest(root)

            self.assertEqual(payload["change_id"], change_id)
            self.assertEqual(payload["digest_kind"], "active")
            self.assertEqual(payload["selected_by"], "current-change")
            self.assertEqual(payload["recommended_reading"]["primary_ref"], str(handoff_path.relative_to(root)))

    def test_resolve_continuity_digest_falls_back_to_last_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-ARCH"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00Z",
                "residual_followups": [],
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "Digest Archived",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })
            closeout_path = Path(materialize_closeout_packet(
                root,
                change_id=change_id,
                closeout_statement="本轮已完成归档",
                delivered_scope=["closeout-packet"],
                deferred_scope=[],
                key_outcomes=["done"],
                unresolved_items=[],
                next_direction="sync",
                attention_points=[],
                carry_forward_items=[],
                operator_summary="archived summary",
                sponsor_summary="archived sponsor",
            ))

            payload = resolve_continuity_digest(root)

            self.assertEqual(payload["change_id"], change_id)
            self.assertEqual(payload["digest_kind"], "archived")
            self.assertEqual(payload["selected_by"], "last-archived-change")
            self.assertEqual(payload["recommended_reading"]["primary_ref"], str(closeout_path.relative_to(root)))

    def test_resolve_continuity_digest_includes_recent_sync_summary_when_history_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-SYNC"
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
                "title": "Digest Sync",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest sync",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest sync.\n", encoding="utf-8")
            materialize_handoff_package(root, change_id)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": change_id,
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "increment",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": f".governance/changes/{change_id}/sync-packet.yaml",
                    "headline": "需要更高层同步",
                }],
            })

            payload = resolve_continuity_digest(root)

            self.assertEqual(payload["recent_sync_summary"]["total_events"], 1)
            self.assertEqual(payload["recent_sync_summary"]["latest_sync_kind"], "escalation")
            self.assertEqual(payload["recent_sync_summary"]["latest_target_layer"], "sponsor")
            self.assertEqual(payload["recent_sync_summary"]["latest_headline"], "需要更高层同步")

    def test_resolve_continuity_digest_includes_grouped_sync_summary_by_target_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-SYNC-GROUPED"
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
                "title": "Digest Sync Grouped",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest sync grouped",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest sync grouped.\n", encoding="utf-8")
            materialize_handoff_package(root, change_id)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": change_id,
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": f".governance/changes/{change_id}/sync-packet-ops.yaml",
                        "headline": "同步到 ops",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": change_id,
                        "recorded_at": "2026-04-24T12:10:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": f".governance/changes/{change_id}/sync-packet-sponsor.yaml",
                        "headline": "同步到 sponsor",
                    },
                    {
                        "event_id": "evt-3",
                        "change_id": change_id,
                        "recorded_at": "2026-04-24T12:20:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": f".governance/changes/{change_id}/sync-packet-sponsor-2.yaml",
                        "headline": "再次同步到 sponsor",
                    },
                ],
            })

            payload = resolve_continuity_digest(root)

            self.assertEqual(payload["recent_sync_grouped_summary"]["group_by"], "target_layer")
            self.assertEqual(payload["recent_sync_grouped_summary"]["groups"][0]["group_key"], "sponsor")
            self.assertEqual(payload["recent_sync_grouped_summary"]["groups"][0]["event_count"], 2)
            self.assertEqual(payload["recent_sync_grouped_summary"]["groups"][1]["group_key"], "ops")

    def test_resolve_continuity_digest_active_includes_projection_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-PROJ-ACTIVE"
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
                "title": "Projection Active",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "projection active",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nProjection active.\n", encoding="utf-8")
            materialize_handoff_package(root, change_id)

            payload = resolve_continuity_digest(root)

            projections = payload["projection_sources"]["summary"]
            self.assertEqual(
                projections["status"]["source_ref"],
                ".governance/runtime/status/change-status.yaml",
            )
            self.assertEqual(projections["status"]["source_field"], "current_status")
            self.assertEqual(
                projections["title"]["source_ref"],
                f".governance/changes/{change_id}/manifest.yaml",
            )

    def test_resolve_continuity_digest_archived_includes_projection_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-PROJ-ARCH"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00Z",
                "residual_followups": [],
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "Projection Archived",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })
            materialize_closeout_packet(
                root,
                change_id=change_id,
                closeout_statement="本轮已完成归档",
                delivered_scope=["closeout-packet"],
                deferred_scope=[],
                key_outcomes=["done"],
                unresolved_items=[],
                next_direction="sync",
                attention_points=[],
                carry_forward_items=[],
                operator_summary="archived summary",
                sponsor_summary="archived sponsor",
            )

            payload = resolve_continuity_digest(root)

            projections = payload["projection_sources"]["summary"]
            self.assertEqual(
                projections["status"]["source_ref"],
                f".governance/archive/{change_id}/closeout-packet.yaml",
            )
            self.assertEqual(projections["status"]["source_field"], "closure_summary.final_status")
            self.assertEqual(
                projections["title"]["source_ref"],
                f".governance/archive/{change_id}/manifest.yaml",
            )

    def test_resolve_continuity_digest_includes_recent_runtime_events_when_timeline_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-DIGEST-RUNTIME-EVENTS"
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
                "title": "Digest Runtime Events",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest runtime events",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest runtime events.\n", encoding="utf-8")
            materialize_handoff_package(root, change_id)
            timeline_dir = root / ".governance/runtime/timeline"
            timeline_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(timeline_dir / "events-202604.yaml", {
                "schema": "runtime-timeline/v1",
                "month": "202604",
                "events": [
                    {
                        "schema": "runtime-event/v1",
                        "event_id": "evt-1",
                        "change_id": change_id,
                        "entity_type": "change",
                        "event_type": "verify_completed",
                        "step": 7,
                        "from_status": "step6-executed-pre-step7",
                        "to_status": "step7-verified",
                        "actor_id": "verifier-agent",
                        "timestamp": "2026-04-24T11:30:00Z",
                        "refs": {"files": [f".governance/changes/{change_id}/verify.yaml"]},
                    },
                    {
                        "schema": "runtime-event/v1",
                        "event_id": "evt-2",
                        "change_id": change_id,
                        "entity_type": "change",
                        "event_type": "review_completed",
                        "step": 8,
                        "from_status": "step7-verified",
                        "to_status": "review-approved",
                        "actor_id": "reviewer-agent",
                        "timestamp": "2026-04-24T12:00:00Z",
                        "refs": {"files": [f".governance/changes/{change_id}/review.yaml"]},
                    },
                ],
                "generated_at": "2026-04-24T12:00:00Z",
            })

            payload = resolve_continuity_digest(root)

            self.assertEqual(len(payload["recent_runtime_events"]), 2)
            self.assertEqual(payload["recent_runtime_events"][-1]["event_type"], "review_completed")
            self.assertEqual(payload["recent_runtime_events"][-1]["to_status"], "review-approved")

    def test_list_sync_history_months_returns_sorted_month_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202605.yaml", {"schema": "sync-history/v1", "month": "202605", "events": []})
            write_yaml(history_dir / "events-202604.yaml", {"schema": "sync-history/v1", "month": "202604", "events": []})

            months = list_sync_history_months(root)

            self.assertEqual(months, ["202604", "202605"])

    def test_read_sync_history_across_all_months_applies_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-X",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "closeout",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/archive/CHG-X/sync-packet.yaml",
                    "headline": "A",
                }],
            })
            write_yaml(history_dir / "events-202605.yaml", {
                "schema": "sync-history/v1",
                "month": "202605",
                "events": [{
                    "event_id": "evt-2",
                    "change_id": "CHG-X",
                    "recorded_at": "2026-05-01T09:00:00Z",
                    "sync_kind": "routine-sync",
                    "source_kind": "increment",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/changes/CHG-X/sync-packet.yaml",
                    "headline": "B",
                }],
            })

            payload = read_sync_history_across_months(root, change_id="CHG-X", source_kind="closeout")

            self.assertEqual(payload["schema"], "sync-history-query/v1")
            self.assertEqual(payload["month"], "all")
            self.assertEqual(payload["months"], ["202604", "202605"])
            self.assertEqual(payload["summary"]["total_events"], 2)
            self.assertEqual(payload["summary"]["matched_events"], 1)
            self.assertEqual(payload["events"][0]["source_kind"], "closeout")

    def test_read_sync_history_returns_empty_payload_when_month_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            payload = read_sync_history(root, month="202604")

            self.assertEqual(payload["schema"], "sync-history-query/v1")
            self.assertEqual(payload["month"], "202604")
            self.assertEqual(payload["summary"]["total_events"], 0)
            self.assertEqual(payload["summary"]["matched_events"], 0)
            self.assertEqual(payload["events"], [])

    def test_read_sync_history_filters_by_change_id_and_source_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-1",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-1/sync-packet.yaml",
                        "headline": "A",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-2",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-2/sync-packet.yaml",
                        "headline": "B",
                    },
                ],
            })

            payload = read_sync_history(root, month="202604", change_id="CHG-1", source_kind="closeout")

            self.assertEqual(payload["summary"]["total_events"], 2)
            self.assertEqual(payload["summary"]["matched_events"], 1)
            self.assertEqual(len(payload["events"]), 1)
            self.assertEqual(payload["events"][0]["change_id"], "CHG-1")
            self.assertEqual(payload["events"][0]["source_kind"], "closeout")

    def test_read_sync_history_across_months_supports_grouped_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-A/sync-packet.yaml",
                        "headline": "A1",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-A/sync-packet.yaml",
                        "headline": "A2",
                    },
                ],
            })
            write_yaml(history_dir / "events-202605.yaml", {
                "schema": "sync-history/v1",
                "month": "202605",
                "events": [{
                    "event_id": "evt-3",
                    "change_id": "CHG-B",
                    "recorded_at": "2026-05-01T09:00:00Z",
                    "sync_kind": "routine-sync",
                    "source_kind": "increment",
                    "target_layer": "ops",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/changes/CHG-B/sync-packet.yaml",
                    "headline": "B1",
                }],
            })

            payload = read_sync_history_across_months(root, summary_by="change_id")

            self.assertEqual(payload["summary"]["matched_events"], 3)
            self.assertEqual(payload["grouped_summary"]["group_by"], "change_id")
            self.assertEqual(len(payload["grouped_summary"]["groups"]), 2)
            self.assertEqual(payload["grouped_summary"]["groups"][0]["group_key"], "CHG-A")
            self.assertEqual(payload["grouped_summary"]["groups"][0]["event_count"], 2)
            self.assertEqual(payload["grouped_summary"]["groups"][0]["latest_headline"], "A2")

    def test_read_sync_history_across_months_supports_summary_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-A",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "closeout",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/archive/CHG-A/sync-packet.yaml",
                    "headline": "A1",
                }],
            })

            payload = read_sync_history_across_months(
                root,
                summary_by="change_id",
                summary_only=True,
            )

            self.assertEqual(payload["summary"]["matched_events"], 1)
            self.assertEqual(payload["grouped_summary"]["group_by"], "change_id")
            self.assertEqual(payload["events"], [])

    def test_read_sync_history_across_months_supports_grouped_summary_by_target_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-A/sync-packet.yaml",
                        "headline": "A1",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-B",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-B/sync-packet.yaml",
                        "headline": "B1",
                    },
                    {
                        "event_id": "evt-3",
                        "change_id": "CHG-C",
                        "recorded_at": "2026-04-24T14:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-C/sync-packet.yaml",
                        "headline": "C1",
                    },
                ],
            })

            payload = read_sync_history_across_months(root, summary_by="target_layer")

            self.assertEqual(payload["grouped_summary"]["group_by"], "target_layer")
            self.assertEqual(payload["grouped_summary"]["groups"][0]["group_key"], "sponsor")
            self.assertEqual(payload["grouped_summary"]["groups"][0]["event_count"], 2)
            self.assertEqual(payload["grouped_summary"]["groups"][1]["group_key"], "ops")

    def test_grouped_summary_exposes_latest_change_and_sync_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-A/sync-packet.yaml",
                        "headline": "A1",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-B",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-B/sync-packet.yaml",
                        "headline": "B1",
                    },
                ],
            })

            payload = read_sync_history_across_months(root, summary_by="target_layer")

            group = payload["grouped_summary"]["groups"][0]
            self.assertEqual(group["group_key"], "sponsor")
            self.assertEqual(group["latest_change_id"], "CHG-B")
            self.assertEqual(group["latest_sync_kind"], "routine-sync")

    def test_grouped_summary_exposes_distinct_change_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-A/sync-packet.yaml",
                        "headline": "A1",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-A",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-A/sync-packet.yaml",
                        "headline": "A2",
                    },
                    {
                        "event_id": "evt-3",
                        "change_id": "CHG-B",
                        "recorded_at": "2026-04-24T14:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-B/sync-packet.yaml",
                        "headline": "B1",
                    },
                ],
            })

            payload = read_sync_history_across_months(root, summary_by="target_layer")

            group = payload["grouped_summary"]["groups"][0]
            self.assertEqual(group["group_key"], "sponsor")
            self.assertEqual(group["event_count"], 3)
            self.assertEqual(group["distinct_change_count"], 2)

    def test_materialize_increment_package_records_delta_and_handoff_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-INCR-1"
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
                "title": "increment package materialization",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "materialize increment package",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["IncrementPackageSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nMaterialize increment package.\n", encoding="utf-8")
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })

            output_path = Path(materialize_increment_package(
                root,
                change_id=change_id,
                reason="post-verify update",
                segment_owner="verifier-agent",
                segment_label="verify-to-review",
                new_findings=["runtime status schema 已稳定"],
                invalidated_assumptions=["timeline 可以只靠生成式补写"],
                new_risks=["owner transfer 尚未进入 review trace"],
                blockers=["review gate still pending"],
                next_followups=["prepare review decision"],
            ))
            payload = load_yaml(output_path)

            self.assertEqual(payload["schema"], "increment-package/v1")
            self.assertEqual(payload["increment_context"]["segment_owner"], "verifier-agent")
            self.assertIn("handoff_package", payload["refs"])
            self.assertTrue((root / f".governance/changes/{change_id}/handoff-package.yaml").exists())

    def test_increment_package_omits_owner_transfer_ref_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-INCR-2"
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
                "title": "increment without owner transfer",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "increment package without owner transfer",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["IncrementPackageSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nIncrement without owner transfer.\n", encoding="utf-8")

            payload = resolve_increment_package(
                root,
                change_id=change_id,
                reason="post-verify update",
                segment_owner="verifier-agent",
                segment_label="verify-to-review",
                new_findings=["runtime status schema 已稳定"],
                invalidated_assumptions=[],
                new_risks=[],
                blockers=[],
                next_followups=[],
            )

            self.assertNotIn("owner_transfer", payload["refs"])

    def test_increment_package_requires_non_empty_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-INCR-3"
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
                "title": "increment empty delta",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "increment empty delta",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["IncrementPackageSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nIncrement empty delta.\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                materialize_increment_package(
                    root,
                    change_id=change_id,
                    reason="empty delta",
                    segment_owner="verifier-agent",
                    segment_label="verify-to-review",
                    new_findings=[],
                    invalidated_assumptions=[],
                    new_risks=[],
                    blockers=[],
                    next_followups=[],
                )



    def test_materialize_closeout_packet_for_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00+00:00",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "closeout packet materialization",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "contract.yaml", {
                "objective": "closeout packet",
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            from governance.continuity import materialize_closeout_packet

            output_path = Path(materialize_closeout_packet(
                root,
                change_id=change_id,
                closeout_statement="本轮已完成最小闭环并正式归档",
                delivered_scope=["continuity primitives"],
                deferred_scope=["sync / escalation packet"],
                key_outcomes=["continuity primitives 形成最小链"],
                unresolved_items=["sync packet 尚未建立"],
                next_direction="build sync / escalation packet",
                attention_points=["不要把 closeout-packet 扩成新的 truth-source"],
                carry_forward_items=["project-to-higher-layer sync"],
                operator_summary="本轮已完成 continuity primitives 基线",
                sponsor_summary="本轮完成 continuity 主线基线",
            ))
            payload = load_yaml(output_path)

            self.assertEqual(payload["schema"], "closeout-packet/v1")
            self.assertEqual(payload["closure_summary"]["final_status"], "archived")
            self.assertEqual(payload["refs"]["archive_receipt"], f".governance/archive/{change_id}/archive-receipt.yaml")

    def test_closeout_packet_rejects_when_archive_map_entry_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-AM-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "missing archive map entry",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            from governance.continuity import materialize_closeout_packet

            with self.assertRaisesRegex(ValueError, "missing from archive-map"):
                materialize_closeout_packet(
                    root,
                    change_id=change_id,
                    closeout_statement="should fail",
                    delivered_scope=["continuity primitives"],
                    deferred_scope=[],
                    key_outcomes=["n/a"],
                    unresolved_items=[],
                    next_direction="n/a",
                    attention_points=[],
                    carry_forward_items=[],
                    operator_summary="n/a",
                    sponsor_summary="n/a",
                )

    def test_closeout_packet_rejects_when_archive_map_receipt_mismatches_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-AM-2"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00+00:00",
                    "receipt": ".governance/archive/CHG-OTHER/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "receipt mismatch",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            from governance.continuity import materialize_closeout_packet

            with self.assertRaisesRegex(ValueError, "receipt does not match"):
                materialize_closeout_packet(
                    root,
                    change_id=change_id,
                    closeout_statement="should fail",
                    delivered_scope=["continuity primitives"],
                    deferred_scope=[],
                    key_outcomes=["n/a"],
                    unresolved_items=[],
                    next_direction="n/a",
                    attention_points=[],
                    carry_forward_items=[],
                    operator_summary="n/a",
                    sponsor_summary="n/a",
                )

    def test_closeout_packet_rejects_when_archive_map_archived_at_mismatches_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-AM-3"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-25T12:00:00+00:00",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "archived_at mismatch",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            from governance.continuity import materialize_closeout_packet

            with self.assertRaisesRegex(ValueError, "archived_at does not match"):
                materialize_closeout_packet(
                    root,
                    change_id=change_id,
                    closeout_statement="should fail",
                    delivered_scope=["continuity primitives"],
                    deferred_scope=[],
                    key_outcomes=["n/a"],
                    unresolved_items=[],
                    next_direction="n/a",
                    attention_points=[],
                    carry_forward_items=[],
                    operator_summary="n/a",
                    sponsor_summary="n/a",
                )

    def test_closeout_packet_rejects_non_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-2"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "not archived yet",
                "status": "step8-reviewed",
                "current_step": 8,
            })

            from governance.continuity import materialize_closeout_packet

            with self.assertRaises(ValueError):
                materialize_closeout_packet(
                    root,
                    change_id=change_id,
                    closeout_statement="should fail",
                    delivered_scope=["continuity primitives"],
                    deferred_scope=[],
                    key_outcomes=["n/a"],
                    unresolved_items=[],
                    next_direction="n/a",
                    attention_points=[],
                    carry_forward_items=[],
                    operator_summary="n/a",
                    sponsor_summary="n/a",
                )



    def test_materialize_sync_packet_from_closeout_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-SYNC-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })

            write_yaml(archive_dir / "closeout-packet.yaml", {
                "schema": "closeout-packet/v1",
                "change_id": change_id,
                "closure_summary": {
                    "final_status": "archived",
                    "closeout_statement": "本轮已完成最小闭环并正式归档",
                },
                "refs": {
                    "runtime_timeline": ".governance/runtime/timeline/events-202604.yaml",
                },
            })

            from governance.continuity import materialize_sync_packet

            output_path = Path(materialize_sync_packet(
                root,
                change_id=change_id,
                source_kind="closeout",
                sync_kind="escalation",
                target_layer="sponsor",
                target_scope="project-level",
                urgency="attention",
                headline="建议进入更高层同步阶段",
                delivered_scope=["closeout-packet"],
                pending_scope=["ecosystem-level sync"],
                requested_attention=["确认上层同步边界"],
                requested_decisions=["是否以 sync-packet 作为默认上层输入"],
                next_owner_suggestion="sponsor-or-ecosystem-operator",
                next_action_suggestion="review sync packet and decide next-level integration",
            ))
            payload = load_yaml(output_path)

            self.assertEqual(payload["schema"], "sync-packet/v1")
            self.assertEqual(payload["source_anchor"]["source_kind"], "closeout")
            self.assertEqual(output_path, archive_dir / "sync-packet.yaml")

    def test_sync_packet_from_closeout_rejects_when_archive_anchor_is_inconsistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-SYNC-AM-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": ".governance/archive/CHG-OTHER/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "closeout-packet.yaml", {
                "schema": "closeout-packet/v1",
                "change_id": change_id,
                "closure_summary": {
                    "final_status": "archived",
                    "closeout_statement": "done",
                },
                "refs": {},
            })

            from governance.continuity import materialize_sync_packet

            with self.assertRaisesRegex(ValueError, "receipt does not match"):
                materialize_sync_packet(
                    root,
                    change_id=change_id,
                    source_kind="closeout",
                    sync_kind="routine-sync",
                    target_layer="sponsor",
                    target_scope="project-level",
                    urgency="normal",
                    headline="sync",
                    delivered_scope=["closeout-packet"],
                    pending_scope=[],
                    requested_attention=[],
                    requested_decisions=[],
                    next_owner_suggestion="owner",
                    next_action_suggestion="review",
                )

    def test_closeout_packet_omits_runtime_change_status_when_active_snapshot_belongs_to_other_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-REF-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00+00:00",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "closeout refs consistency",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })
            runtime_status_dir = root / ".governance/runtime/status"
            runtime_status_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(runtime_status_dir / "change-status.yaml", {
                "schema": "runtime-change-status/v1",
                "change_id": "CHG-OTHER",
                "current_status": "step7-verified",
                "current_step": 7,
                "phase": "执行与验证",
            })
            write_yaml(runtime_status_dir / "steps-status.yaml", {
                "schema": "runtime-steps-status/v1",
                "change_id": "CHG-OTHER",
                "current_step": 7,
                "steps": [],
            })
            write_yaml(runtime_status_dir / "participants-status.yaml", {
                "schema": "runtime-participants-status/v1",
                "change_id": "CHG-OTHER",
                "participants": [],
            })

            from governance.continuity import resolve_closeout_packet

            payload = resolve_closeout_packet(
                root,
                change_id=change_id,
                closeout_statement="closeout",
                delivered_scope=["continuity"],
                deferred_scope=[],
                key_outcomes=["done"],
                unresolved_items=[],
                next_direction="sync",
                attention_points=[],
                carry_forward_items=[],
                operator_summary="ok",
                sponsor_summary="ok",
            )

            self.assertNotIn("runtime_change_status", payload["refs"])

    def test_closeout_packet_omits_runtime_timeline_ref_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLOSE-REF-2"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00+00:00",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "closeout refs consistency",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            from governance.continuity import resolve_closeout_packet

            payload = resolve_closeout_packet(
                root,
                change_id=change_id,
                closeout_statement="closeout",
                delivered_scope=["continuity"],
                deferred_scope=[],
                key_outcomes=["done"],
                unresolved_items=[],
                next_direction="sync",
                attention_points=[],
                carry_forward_items=[],
                operator_summary="ok",
                sponsor_summary="ok",
            )

            self.assertNotIn("runtime_timeline", payload["refs"])

    def test_materialize_sync_packet_from_increment_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-SYNC-2"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(change_dir / "increment-package.yaml", {
                "schema": "increment-package/v1",
                "change_id": change_id,
                "state_anchor": {
                    "current_status": "step7-verified",
                    "next_decision": "Step 8 / Review and decide",
                },
                "refs": {
                    "runtime_timeline": ".governance/runtime/timeline/events-202604.yaml",
                },
            })

            from governance.continuity import materialize_sync_packet

            output_path = Path(materialize_sync_packet(
                root,
                change_id=change_id,
                source_kind="increment",
                sync_kind="routine-sync",
                target_layer="sponsor",
                target_scope="project-level",
                urgency="normal",
                headline="阶段增量同步",
                delivered_scope=["increment-package"],
                pending_scope=[],
                requested_attention=[],
                requested_decisions=[],
                next_owner_suggestion="reviewer",
                next_action_suggestion="review increment result",
            ))
            payload = load_yaml(output_path)

            self.assertEqual(payload["source_anchor"]["source_kind"], "increment")
            self.assertEqual(output_path, change_dir / "sync-packet.yaml")

    def test_sync_packet_omits_runtime_timeline_when_source_ref_target_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-SYNC-REF-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "closeout-packet.yaml", {
                "schema": "closeout-packet/v1",
                "change_id": change_id,
                "closure_summary": {
                    "final_status": "archived",
                    "closeout_statement": "done",
                },
                "refs": {
                    "runtime_timeline": ".governance/runtime/timeline/events-202604.yaml",
                },
            })

            from governance.continuity import resolve_sync_packet

            payload = resolve_sync_packet(
                root,
                change_id=change_id,
                source_kind="closeout",
                sync_kind="routine-sync",
                target_layer="sponsor",
                target_scope="project-level",
                urgency="normal",
                headline="sync",
                delivered_scope=["closeout-packet"],
                pending_scope=[],
                requested_attention=[],
                requested_decisions=[],
                next_owner_suggestion="owner",
                next_action_suggestion="review",
            )

            self.assertNotIn("runtime_timeline", payload["refs"])

    def test_increment_package_omits_runtime_timeline_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-INC-REF-1"
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
                "title": "increment refs consistency",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "increment refs consistency",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["IncrementPackageSchema"],
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
            (change_dir / "tasks.md").write_text("# Tasks\n\nIncrement refs.\n", encoding="utf-8")

            from governance.continuity import resolve_increment_package

            payload = resolve_increment_package(
                root,
                change_id=change_id,
                reason="ref consistency",
                segment_owner="verifier-agent",
                segment_label="verify",
                new_findings=["timeline omitted when missing"],
                invalidated_assumptions=[],
                new_risks=[],
                blockers=[],
                next_followups=["review refs"],
            )

            self.assertNotIn("runtime_timeline", payload["refs"])

    def test_sync_packet_requires_attention_or_decision_for_escalation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-SYNC-3"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "closeout-packet.yaml", {
                "schema": "closeout-packet/v1",
                "change_id": change_id,
                "closure_summary": {"final_status": "archived", "closeout_statement": "done"},
                "refs": {},
            })

            from governance.continuity import materialize_sync_packet

            with self.assertRaises(ValueError):
                materialize_sync_packet(
                    root,
                    change_id=change_id,
                    source_kind="closeout",
                    sync_kind="escalation",
                    target_layer="sponsor",
                    target_scope="project-level",
                    urgency="attention",
                    headline="需要升级",
                    delivered_scope=["closeout-packet"],
                    pending_scope=[],
                    requested_attention=[],
                    requested_decisions=[],
                    next_owner_suggestion="sponsor",
                    next_action_suggestion="decide next step",
                )



    def test_append_sync_history_from_closeout_sync_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HIST-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "sync-packet.yaml", {
                "schema": "sync-packet/v1",
                "change_id": change_id,
                "generated_at": "2026-04-24T12:00:00Z",
                "sync_kind": "escalation",
                "source_anchor": {"source_kind": "closeout"},
                "target_context": {"target_layer": "sponsor", "target_scope": "project-level"},
                "sync_summary": {"headline": "需要更高层同步"},
            })

            from governance.continuity import append_sync_history

            output_path = Path(append_sync_history(root, change_id=change_id, source_kind="closeout"))
            payload = load_yaml(output_path)
            self.assertEqual(payload["schema"], "sync-history/v1")
            self.assertEqual(len(payload["events"]), 1)
            self.assertEqual(payload["events"][0]["packet_ref"], f".governance/archive/{change_id}/sync-packet.yaml")

    def test_append_sync_history_deduplicates_same_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-HIST-2"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "sync-packet.yaml", {
                "schema": "sync-packet/v1",
                "change_id": change_id,
                "generated_at": "2026-04-24T12:00:00Z",
                "sync_kind": "routine-sync",
                "source_anchor": {"source_kind": "closeout"},
                "target_context": {"target_layer": "sponsor", "target_scope": "project-level"},
                "sync_summary": {"headline": "阶段同步"},
            })

            from governance.continuity import append_sync_history

            output_path = Path(append_sync_history(root, change_id=change_id, source_kind="closeout"))
            append_sync_history(root, change_id=change_id, source_kind="closeout")
            payload = load_yaml(output_path)
            self.assertEqual(len(payload["events"]), 1)

    def test_export_sync_packet_writes_minimum_external_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_root = root / "exports"
            ensure_governance_index(root)
            change_id = "CHG-EXP-1"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "sync-packet.yaml", {
                "schema": "sync-packet/v1",
                "change_id": change_id,
                "generated_at": "2026-04-24T12:00:00Z",
                "sync_kind": "escalation",
                "source_anchor": {"source_kind": "closeout"},
                "target_context": {"target_layer": "sponsor", "target_scope": "project-level"},
                "sync_summary": {"headline": "需要更高层同步"},
            })

            from governance.continuity import export_sync_packet

            export_dir = Path(export_sync_packet(root, change_id=change_id, source_kind="closeout", output_dir=export_root))
            self.assertTrue((export_dir / "README.md").exists())
            self.assertTrue((export_dir / "export-manifest.yaml").exists())
            self.assertTrue((export_dir / "sync-packet.yaml").exists())

    def test_export_sync_packet_fails_when_source_packet_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_root = root / "exports"
            ensure_governance_index(root)

            from governance.continuity import export_sync_packet

            with self.assertRaises(ValueError):
                export_sync_packet(root, change_id="CHG-EXP-2", source_kind="closeout", output_dir=export_root)

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
