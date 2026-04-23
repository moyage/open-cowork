from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.continuity import (
    materialize_continuity_launch_input,
    materialize_round_entry_input_summary,
    resolve_continuity_launch_input,
    resolve_round_entry_input_summary,
)
from governance.index import ensure_governance_index, set_current_change, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class ContinuityTests(unittest.TestCase):
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
