from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.evidence import ensure_required_evidence
from governance.index import ensure_governance_index
from governance.simple_yaml import load_yaml, write_yaml


class V032RuntimeCoherenceTests(unittest.TestCase):
    def test_step5_approval_reconciles_manifest_validation_objects_before_step6_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V032-STEP6", current_step=5, status="step5-prepared")
            change_dir = root / ".governance/changes/CHG-V032-STEP6"
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["target_validation_objects"] = ["docs/old-step-report.md"]
            write_yaml(change_dir / "manifest.yaml", manifest)
            write_yaml(change_dir / "human-gates.yaml", {"approvals": {}})

            output = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V032-STEP6",
                "--step",
                "5",
                "--approved-by",
                "human-sponsor",
            )
            self.assertIn("Step 5 approved", output)

            status_output = self._run_cli(root, "status", "--change-id", "CHG-V032-STEP6")
            self.assertIn("current_step: 6", status_output)
            self.assertIn("## Blockers\n- none", status_output)
            reconciled = load_yaml(change_dir / "manifest.yaml")
            contract = load_yaml(change_dir / "contract.yaml")
            self.assertEqual(reconciled["target_validation_objects"], contract["validation_objects"])

    def test_participants_list_shows_runtime_type_availability_and_review_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V032-PARTICIPANTS", current_step=6, status="step6-in-progress")
            write_yaml(root / ".governance/participants.yaml", {
                "schema": "participants-profile/v1",
                "profile": "personal",
                "participants": [
                    {"id": "legacy-reviewer", "type": "agent", "strengths": ["legacy-profile"]},
                ],
                "step_owner_matrix": [
                    {"step": 8, "primary_owner": "legacy-reviewer", "reviewer": "legacy-reviewer", "human_gate": True},
                ],
            })

            output = self._run_cli(
                root,
                "participants",
                "list",
                "--change-id",
                "CHG-V032-PARTICIPANTS",
                "--format",
                "human",
            )
            self.assertIn("codex-agent (runtime_participant, availability=active-current-session)", output)
            self.assertIn("hermes-agent (external_reviewer, availability=not-probed)", output)
            self.assertIn("Step 8: owner=hermes-agent runtime_reviewer=hermes-agent fallback_reviewer=ooso-omoc-agent human_gate=true", output)

    def test_last_archive_summary_is_short_and_points_to_final_status_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            archive_dir = root / ".governance/archive/CHG-V032-ARCHIVE"
            archive_dir.mkdir(parents=True)
            write_yaml(root / ".governance/index/current-change.yaml", {"schema": "current-change/v1", "change_id": None, "status": "idle", "current_step": None})
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "last_archived_change": "CHG-V032-ARCHIVE",
                "last_archive_at": "2026-04-27T00:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "archive_executed": True,
                "change_id": "CHG-V032-ARCHIVE",
                "traceability": {"final_status_snapshot": ".governance/archive/CHG-V032-ARCHIVE/FINAL_STATUS_SNAPSHOT.yaml"},
            })
            write_yaml(archive_dir / "review.yaml", {"decision": {"status": "approve", "rationale": "ready"}})
            write_yaml(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml", {"status": "pass", "human_gate_summary": {}})
            write_yaml(archive_dir / "FINAL_STATUS_SNAPSHOT.yaml", {
                "schema": "final-status-snapshot/v1",
                "change_id": "CHG-V032-ARCHIVE",
                "final_status": "archived",
                "review_decision": "approve",
                "final_consistency": "pass",
            })

            output = self._run_cli(root, "status", "--last-archive")
            self.assertIn("final_status_snapshot: .governance/archive/CHG-V032-ARCHIVE/FINAL_STATUS_SNAPSHOT.yaml", output)
            self.assertLess(len(output.splitlines()), 20)

    def test_custom_required_evidence_can_be_satisfied_by_named_evidence_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_dir = root / ".governance/changes/CHG-V032-EVIDENCE/evidence"
            evidence_dir.mkdir(parents=True)
            for name in [
                "step-report-output.yaml",
                "human-gate-trace.yaml",
                "review-lifecycle-trace.yaml",
                "runtime-agent-probe-or-fallback-trace.yaml",
            ]:
                write_yaml(evidence_dir / name, {"status": "recorded"})

            ensure_required_evidence(
                [
                    "step_report_output",
                    "human_gate_trace",
                    "review_lifecycle_trace",
                    "runtime_agent_probe_or_fallback_trace",
                ],
                {},
                [
                    str(evidence_dir / "step-report-output.yaml"),
                    str(evidence_dir / "human-gate-trace.yaml"),
                    str(evidence_dir / "review-lifecycle-trace.yaml"),
                    str(evidence_dir / "runtime-agent-probe-or-fallback-trace.yaml"),
                ],
            )

    def _run_cli(self, root: Path, *args: str) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, 0, output)
        return output

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
        validation_objects = [
            "src/governance/status_views.py",
            "src/governance/step_report.py",
            "tests/test_v032.py",
        ]
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "target_validation_objects": validation_objects,
            "readiness": {"step6_entry_ready": current_step >= 6, "missing_items": []},
            "roles": {"executor": "codex-agent", "verifier": "verifier-agent", "reviewer": "hermes-agent"},
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "title": change_id,
            "objective": "v0.3.2 runtime coherence",
            "scope_in": ["src/governance/**", "tests/**", f".governance/changes/{change_id}/**"],
            "scope_out": [".governance/archive/**", ".governance/runtime/**"],
            "allowed_actions": ["edit_files", "run_commands", "write_evidence"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
                "no_fake_local_agent_review",
            ],
            "validation_objects": validation_objects,
            "verification": {"commands": ["python3 -m unittest discover -s tests"], "checks": ["v032"]},
            "evidence_expectations": {"required": ["changed_files_manifest", "test_output_summary"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "participants": [
                {"id": "human-sponsor", "type": "human_participant", "availability": "available"},
                {"id": "codex-agent", "type": "runtime_participant", "availability": "active-current-session"},
                {"id": "hermes-agent", "type": "external_reviewer", "availability": "not-probed"},
                {"id": "ooso-omoc-agent", "type": "fallback_runtime", "availability": "not-probed"},
            ],
            "steps": {
                "5": {"owner": "human-sponsor", "gate": "human-approval", "human_gate": True},
                "6": {"owner": "codex-agent", "reviewer": "verifier-agent", "gate": "execution-evidence", "human_gate": False},
                "7": {"owner": "verifier-agent", "reviewer": "hermes-agent", "gate": "verification-review", "human_gate": False},
                "8": {
                    "owner": "hermes-agent",
                    "runtime_reviewer": "hermes-agent",
                    "fallback_reviewer": "ooso-omoc-agent",
                    "human_gate_approver": "human-sponsor",
                    "human_gate": True,
                    "gate": "review-and-human-approval",
                },
                "9": {"owner": "maintainer-agent", "reviewer": "human-sponsor", "gate": "archive-approval", "human_gate": True},
            },
        })
        (change_dir / "tasks.md").write_text("# Tasks\n\nDeliver v0.3.2 runtime coherence.\n", encoding="utf-8")
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step},
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })


if __name__ == "__main__":
    unittest.main()
