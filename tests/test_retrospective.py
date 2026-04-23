from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.retrospective import build_post_round_retrospective, materialize_post_round_retrospective
from governance.simple_yaml import load_yaml, write_yaml


class RetrospectiveTests(unittest.TestCase):
    def test_materialize_post_round_retrospective_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_dir = root / ".governance/changes/CHG-2"
            archive_dir = root / ".governance/archive/CHG-1"
            index_dir = root / ".governance/index"
            change_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.mkdir(parents=True, exist_ok=True)
            index_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(index_dir / "current-change.yaml", {"current_change_id": "CHG-2"})
            write_yaml(index_dir / "maintenance-status.yaml", {
                "current_change_id": "CHG-2",
                "last_archived_change": "CHG-1",
                "residual_followups": [{"id": "R1", "note": "carry forward summary evidence limitation"}],
            })
            write_yaml(change_dir / "manifest.yaml", {
                "id": "CHG-2",
                "target_validation_objects": [
                    "StateConsistencyCheck",
                    "StepMatrixView",
                    "PostRoundRetrospectiveAndIterationSynthesis",
                ],
            })
            write_yaml(change_dir / "contract.yaml", {
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "archive_executed": True,
                "archived_at": "2026-04-21T00:00:00Z",
                "traceability": {"step8_review": ".governance/archive/CHG-1/review.yaml"},
                "residual_followups": [{"id": "A1", "note": "archive-level carry forward"}],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "title": "Archived Round",
                "status": "archived",
                "lifecycle": {"step9": {"status": "completed"}},
            })
            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve_with_conditions"},
                "conditions": {"followups": ["tighten telemetry hygiene"]},
            })

            payload = build_post_round_retrospective(root, "CHG-2", "CHG-1")
            written = materialize_post_round_retrospective(root, "CHG-2", "CHG-1")

            self.assertTrue(Path(written["yaml"]).exists())
            self.assertTrue(Path(written["markdown"]).exists())
            persisted = load_yaml(Path(written["yaml"]))
            self.assertEqual(payload["source_archived_change_id"], "CHG-1")
            self.assertEqual(persisted["generated_for_change_id"], "CHG-2")
            self.assertIn("StateConsistencyCheck", persisted["iteration_synthesis"]["candidate_requirements"])
            self.assertTrue(persisted["residual_carry_forward"])


if __name__ == "__main__":
    unittest.main()
