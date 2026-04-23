from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.index import (
    ensure_governance_index,
    read_changes_index,
    read_current_change,
    set_current_change,
    set_maintenance_status,
    upsert_change_entry,
)


class GovernanceIndexTests(unittest.TestCase):
    def test_ensure_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_current_change(root, {"change_id": "CHG-1", "path": ".governance/changes/CHG-1", "status": "drafting", "current_step": 5})
            upsert_change_entry(root, {"change_id": "CHG-1", "path": ".governance/changes/CHG-1", "status": "drafting", "current_step": 5})
            self.assertEqual(read_current_change(root)["current_change"]["change_id"], "CHG-1")
            self.assertEqual(read_changes_index(root)["changes"][0]["change_id"], "CHG-1")

    def test_set_current_change_blocks_regression_for_same_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_current_change(root, {
                "change_id": "CHG-1",
                "path": ".governance/changes/CHG-1",
                "status": "step7-verified",
                "current_step": 7,
            })

            with self.assertRaisesRegex(ValueError, "cannot regress"):
                set_current_change(root, {
                    "change_id": "CHG-1",
                    "path": ".governance/changes/CHG-1",
                    "status": "step6-executed-pre-step7",
                    "current_step": 6,
                })

    def test_upsert_change_entry_blocks_regression_for_same_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            upsert_change_entry(root, {
                "change_id": "CHG-1",
                "path": ".governance/changes/CHG-1",
                "status": "review-approved",
                "current_step": 8,
            })

            with self.assertRaisesRegex(ValueError, "cannot regress"):
                upsert_change_entry(root, {
                    "change_id": "CHG-1",
                    "path": ".governance/changes/CHG-1",
                    "status": "step7-verified",
                    "current_step": 7,
                })

    def test_set_current_change_allows_switching_to_different_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_current_change(root, {
                "change_id": "CHG-1",
                "path": ".governance/changes/CHG-1",
                "status": "review-approved",
                "current_step": 8,
            })

            payload = set_current_change(root, {
                "change_id": "CHG-2",
                "path": ".governance/changes/CHG-2",
                "status": "drafting",
                "current_step": 5,
            })
            self.assertEqual(payload["current_change_id"], "CHG-2")

    def test_set_current_change_allows_idle_clear_after_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_current_change(root, {
                "change_id": "CHG-1",
                "path": ".governance/changes/CHG-1",
                "status": "archived",
                "current_step": 9,
            })

            payload = set_current_change(root, {
                "change_id": None,
                "status": "idle",
                "current_step": None,
            })
            self.assertEqual(payload["status"], "idle")

    def test_set_maintenance_status_blocks_status_regression_for_same_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="step7-verified",
                current_change_active="step7-verified",
                current_change_id="CHG-1",
            )

            with self.assertRaisesRegex(ValueError, "cannot regress"):
                set_maintenance_status(
                    root,
                    status="step6-executed-pre-step7",
                    current_change_active="step6-executed-pre-step7",
                    current_change_id="CHG-1",
                )

    def test_set_maintenance_status_allows_switching_to_different_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="step7-verified",
                current_change_active="step7-verified",
                current_change_id="CHG-1",
            )

            payload = set_maintenance_status(
                root,
                status="drafting",
                current_change_active="draft",
                current_change_id="CHG-2",
            )
            self.assertEqual(payload["current_change_id"], "CHG-2")

    def test_set_maintenance_status_allows_idle_clear_after_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="review-approved",
                current_change_active="review-approved",
                current_change_id="CHG-1",
            )

            payload = set_maintenance_status(
                root,
                status="idle",
                current_change_active="none",
                current_change_id=None,
                last_archived_change="CHG-1",
                last_archive_at="2026-04-24T12:00:00+00:00",
            )
            self.assertEqual(payload["status"], "idle")
            self.assertEqual(payload["last_archived_change"], "CHG-1")

    def test_set_maintenance_status_blocks_clearing_last_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="idle",
                current_change_active="none",
                current_change_id=None,
                last_archived_change="CHG-1",
                last_archive_at="2026-04-24T12:00:00+00:00",
            )

            with self.assertRaisesRegex(ValueError, "cannot clear"):
                set_maintenance_status(root, last_archived_change=None)

    def test_set_maintenance_status_blocks_clearing_last_archive_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="idle",
                current_change_active="none",
                current_change_id=None,
                last_archived_change="CHG-1",
                last_archive_at="2026-04-24T12:00:00+00:00",
            )

            with self.assertRaisesRegex(ValueError, "cannot clear"):
                set_maintenance_status(root, last_archive_at=None)

    def test_set_maintenance_status_allows_replacing_archive_baseline_with_new_non_empty_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            set_maintenance_status(
                root,
                status="idle",
                current_change_active="none",
                current_change_id=None,
                last_archived_change="CHG-1",
                last_archive_at="2026-04-24T12:00:00+00:00",
            )

            payload = set_maintenance_status(
                root,
                last_archived_change="CHG-2",
                last_archive_at="2026-04-25T12:00:00+00:00",
            )
            self.assertEqual(payload["last_archived_change"], "CHG-2")


if __name__ == "__main__":
    unittest.main()
