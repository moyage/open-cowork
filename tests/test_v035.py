from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index
from governance.simple_yaml import load_yaml, write_yaml


class V035DogfoodCleanupTests(unittest.TestCase):
    def test_step_reports_project_authoritative_scope_when_intent_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V035-FACTS", "--title", "Facts")
            self._run_cli(
                root,
                "change",
                "prepare",
                "CHG-V035-FACTS",
                "--goal",
                "Decision facts",
                "--scope-in",
                "src/**",
                "--verify-command",
                "python3 -c 'print(\"ok\")'",
            )

            report = load_yaml(root / ".governance/changes/CHG-V035-FACTS/step-reports/step-3.yaml")

            self.assertEqual(report["intent_summary"]["project_intent"], "Decision facts")
            self.assertIn("src/**", report["intent_summary"]["scope_in"])
            self.assertEqual(report["intent_summary"]["facts_source"], "contract")
            self.assertIn("python3 -c 'print(\"ok\")'", report["artifact_summary"]["verification_commands"])

    def test_intent_confirm_satisfies_step1_and_non_gate_step_can_be_acknowledged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V035-ACK", "--title", "Acknowledgement")
            self._run_cli(root, "change", "prepare", "CHG-V035-ACK", "--goal", "Acknowledge human work")

            step4 = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V035-ACK",
                "--step",
                "4",
                "--approved-by",
                "human-sponsor",
                "--note",
                "tasks reviewed",
            )
            self.assertIn("Step 4 acknowledged", step4)
            gates = load_yaml(root / ".governance/changes/CHG-V035-ACK/human-gates.yaml")
            self.assertEqual(gates["acknowledgements"][0]["step"], 4)
            self.assertNotIn(4, gates.get("approvals", {}))

            self._run_cli(root, "intent", "confirm", "--change-id", "CHG-V035-ACK", "--confirmed-by", "human-sponsor")
            output = self._run_cli(
                root,
                "step",
                "approve",
                "--change-id",
                "CHG-V035-ACK",
                "--step",
                "2",
                "--approved-by",
                "human-sponsor",
            )
            self.assertIn("Step 2 approved", output)
            gates = load_yaml(root / ".governance/changes/CHG-V035-ACK/human-gates.yaml")
            self.assertEqual((gates["approvals"].get(1) or gates["approvals"].get("1"))["source"], "intent-confirm")

    def test_review_decision_can_be_recorded_before_step8_human_acceptance_but_archive_requires_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_verified_change(root, "CHG-V035-REVIEW")

            review = self._run_cli(
                root,
                "review",
                "--change-id",
                "CHG-V035-REVIEW",
                "--decision",
                "approve",
                "--reviewer",
                "hermes-agent",
                "--rationale",
                "ready",
            )
            self.assertIn("Review recorded: CHG-V035-REVIEW -> review-approved", review)

            archive_fail = self._run_cli(
                root,
                "archive",
                "--change-id",
                "CHG-V035-REVIEW",
                expect=1,
            )
            self.assertIn("Step 8 human gate approval is required", archive_fail)

            self._run_cli(root, "step", "approve", "--change-id", "CHG-V035-REVIEW", "--step", "8", "--approved-by", "human-sponsor")
            self._run_cli(root, "step", "approve", "--change-id", "CHG-V035-REVIEW", "--step", "9", "--approved-by", "human-sponsor")
            archive_ok = self._run_cli(root, "archive", "--change-id", "CHG-V035-REVIEW")
            self.assertIn("Archived change CHG-V035-REVIEW", archive_ok)

    def test_verify_can_execute_contract_commands_and_records_state_only_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_executed_change(root, "CHG-V035-VERIFY")
            self._run_cli(root, "verify", "--change-id", "CHG-V035-VERIFY")
            state_only = load_yaml(root / ".governance/changes/CHG-V035-VERIFY/verify.yaml")
            self.assertEqual(state_only["product_verification"]["mode"], "state-only")
            self.assertEqual(state_only["product_verification"]["commands"][0]["status"], "not-run")

            self._write_executed_change(root, "CHG-V035-VERIFY-RUN")
            self._run_cli(root, "verify", "--change-id", "CHG-V035-VERIFY-RUN", "--run-commands")
            product = load_yaml(root / ".governance/changes/CHG-V035-VERIFY-RUN/verify.yaml")
            self.assertEqual(product["product_verification"]["mode"], "commands-executed")
            self.assertEqual(product["product_verification"]["commands"][0]["status"], "pass")
            self.assertIn("v035-product-ok", product["product_verification"]["commands"][0]["stdout"])

    def test_prepare_records_dirty_baseline_and_docs_tree_is_curated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run("git", "init", cwd=root)
            (root / "dirty.txt").write_text("baseline noise\n", encoding="utf-8")
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V035-BASELINE", "--title", "Baseline")
            self._run_cli(root, "change", "prepare", "CHG-V035-BASELINE", "--goal", "Baseline separation")

            baseline = load_yaml(root / ".governance/changes/CHG-V035-BASELINE/baseline.yaml")

            self.assertTrue(baseline["dirty"])
            self.assertIn("dirty.txt", "\n".join(baseline["git_status_entries"]))

        project_root = Path(__file__).resolve().parents[1]
        self.assertFalse((project_root / "docs/plans").exists())
        self.assertFalse((project_root / "docs/reports").exists())
        self.assertFalse((project_root / "docs/archive/plans").exists())
        self.assertFalse((project_root / "docs/archive/reports").exists())
        spec_files = sorted(path.name for path in (project_root / "docs/specs").glob("*.md"))
        self.assertEqual(spec_files, [
            "00-overview.md",
            "01-runtime-flow.md",
            "02-change-package-and-contract.md",
            "03-evidence-review-archive.md",
            "04-agent-adoption-and-doc-governance.md",
            "README.md",
        ])

    def test_change_prepare_reuses_existing_intent_goal_when_goal_argument_is_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V035-GOAL", "--title", "Existing goal")
            self._run_cli(
                root,
                "intent",
                "capture",
                "--change-id",
                "CHG-V035-GOAL",
                "--project-intent",
                "Reuse captured intent",
            )

            self._run_cli(root, "change", "prepare", "CHG-V035-GOAL")

            contract = load_yaml(root / ".governance/changes/CHG-V035-GOAL/contract.yaml")
            self.assertEqual(contract["objective"], "Reuse captured intent")

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output

    def _run(self, *args: str, cwd: Path) -> str:
        import subprocess

        return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout

    def _write_executed_change(self, root: Path, change_id: str) -> None:
        self._write_change(root, change_id, current_step=6, status="step6-executed-pre-step7")
        write_yaml(root / f".governance/changes/{change_id}/evidence/execution-summary.yaml", {
            "status": "complete",
            "artifacts": {"created": [], "modified": []},
        })

    def _write_verified_change(self, root: Path, change_id: str) -> None:
        self._write_change(root, change_id, current_step=7, status="step7-verified")
        write_yaml(root / f".governance/changes/{change_id}/verify.yaml", {
            "summary": {"status": "pass", "blocker_count": 0},
            "checks": [],
            "issues": [],
        })
        write_yaml(root / f".governance/changes/{change_id}/human-gates.yaml", {"schema": "human-gates/v1", "change_id": change_id, "approvals": {}})

    def _write_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "target_validation_objects": ["src/governance/verify.py"],
            "readiness": {"step6_entry_ready": current_step >= 6, "missing_items": []},
            "roles": {"executor": "codex-agent", "reviewer": "hermes-agent"},
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "title": change_id,
            "objective": "v0.3.5 dogfood closure",
            "scope_in": ["src/**", "tests/**", f".governance/changes/{change_id}/evidence/**"],
            "scope_out": [".governance/archive/**", ".governance/runtime/**"],
            "allowed_actions": ["edit_files", "run_commands", "write_evidence"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["src/governance/verify.py"],
            "verification": {"commands": ["python3 -c 'print(\"v035-product-ok\")'"], "checks": ["v035"]},
            "evidence_expectations": {"required": ["command_output", "test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "5": {"owner": "human-sponsor", "human_gate": True, "gate": "approval-required"},
                "6": {"owner": "codex-agent", "human_gate": False, "gate": "execution"},
                "7": {"owner": "verifier-agent", "human_gate": False, "gate": "verify"},
                "8": {"owner": "hermes-agent", "reviewer": "hermes-agent", "human_gate": True, "gate": "review-acceptance"},
                "9": {"owner": "maintainer-agent", "reviewer": "human-sponsor", "human_gate": True, "gate": "archive"},
            }
        })
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
