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


if __name__ == "__main__":
    unittest.main()
