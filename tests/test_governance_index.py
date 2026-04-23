from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.index import ensure_governance_index, read_changes_index, read_current_change, set_current_change, upsert_change_entry


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


if __name__ == "__main__":
    unittest.main()
