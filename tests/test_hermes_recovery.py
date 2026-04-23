from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.hermes_recovery import (
    diagnose_hermes_execution_stall,
    materialize_hermes_recovery_packet,
)
from governance.simple_yaml import load_yaml, write_yaml


class HermesRecoveryTests(unittest.TestCase):
    def test_idle_post_close_diagnosis_and_packet_materialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = root / ".governance/index"
            change_dir = root / ".governance/changes/CHG-1"
            archive_dir = root / ".governance/archive/CHG-1"
            docs_dir = root / "docs/specs"
            index_dir.mkdir(parents=True, exist_ok=True)
            change_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.mkdir(parents=True, exist_ok=True)
            docs_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(index_dir / "current-change.yaml", {
                "schema": "current-change/v1",
                "status": "idle",
                "current_change": None,
            })
            write_yaml(index_dir / "maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": "CHG-1",
                "last_archive_at": "2026-04-23T02:38:33Z",
            })
            write_yaml(index_dir / "archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": "CHG-1",
                    "archive_path": ".governance/archive/CHG-1/",
                    "receipt": ".governance/archive/CHG-1/archive-receipt.yaml",
                }],
            })

            change_manifest = {"id": "CHG-1", "status": "archived"}
            write_yaml(change_dir / "manifest.yaml", change_manifest)
            write_yaml(archive_dir / "manifest.yaml", change_manifest)
            review_payload = {"decision": {"status": "approved"}}
            write_yaml(change_dir / "review.yaml", review_payload)
            write_yaml(archive_dir / "review.yaml", review_payload)
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True})
            write_yaml(archive_dir / "verify.yaml", {"checks": []})
            write_yaml(archive_dir / "STATE_CONSISTENCY_CHECK.yaml", {"status": "pass"})
            write_yaml(archive_dir / "ROUND_ENTRY_INPUT_SUMMARY.yaml", {"change_id": "CHG-1"})
            (archive_dir / "STEP_MATRIX_VIEW.md").write_text("# matrix\n", encoding="utf-8")
            (archive_dir / "ROUND5_CLOSE_OUT_SUMMARY.yaml").write_text("schema: round-close-out-summary/v1\n", encoding="utf-8")
            (docs_dir / "oversized.md").write_text("context " * 5000, encoding="utf-8")

            diagnosis = diagnose_hermes_execution_stall(root, context_budget_tokens=800)

            self.assertEqual(diagnosis["lifecycle_phase"], "idle_post_close")
            self.assertIn("RC1_CLOSE_REENTRY_ON_IDLE", [item["id"] for item in diagnosis["root_causes"]])
            self.assertIn("RC2_DUPLICATE_READ_SURFACE", [item["id"] for item in diagnosis["root_causes"]])
            self.assertIn("RC3_CONTEXT_BUDGET_EXCEEDED", [item["id"] for item in diagnosis["root_causes"]])
            self.assertTrue(diagnosis["duplicate_surface"]["identical_count"] >= 2)
            self.assertTrue(diagnosis["context_budget"]["full_scan_estimated_tokens"] > diagnosis["context_budget"]["budget_tokens"])
            self.assertTrue(all(
                item["path"].startswith(".governance/archive/CHG-1/")
                or item["path"].startswith(".governance/index/")
                for item in diagnosis["recommended_read_set"]
            ))

            packet_path = Path(materialize_hermes_recovery_packet(root, context_budget_tokens=800))
            payload = load_yaml(packet_path)
            self.assertEqual(payload["schema"], "governance/session-recovery-diagnosis/v1")
            self.assertEqual(payload["lifecycle_phase"], "idle_post_close")

    def test_diagnosis_without_archive_context_returns_safe_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = root / ".governance/index"
            index_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(index_dir / "current-change.yaml", {
                "schema": "current-change/v1",
                "status": "idle",
                "current_change": None,
            })
            diagnosis = diagnose_hermes_execution_stall(root)

            self.assertEqual(diagnosis["lifecycle_phase"], "idle_no_archive")
            self.assertIsNone(diagnosis["target_change_id"])
            self.assertTrue(any(item["id"] == "RC0_NO_HARD_BLOCKER_FOUND" for item in diagnosis["root_causes"]))
            self.assertTrue(any(item["path"] == ".governance/index/current-change.yaml" for item in diagnosis["recommended_read_set"]))


if __name__ == "__main__":
    unittest.main()
