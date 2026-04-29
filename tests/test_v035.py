from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class V035ProjectActivationTests(unittest.TestCase):
    def test_parallel_active_changes_can_be_explicitly_activated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "REQ-1", "需求 1")
            self._prepare(root, "REQ-2", "需求 2")

            active = load_yaml(root / ".governance/index/active-changes.yaml")
            active_ids = {item["change_id"] for item in active["changes"]}
            self.assertEqual(active_ids, {"REQ-1", "REQ-2"})

            ambiguous = self._run_cli(root, "activate")
            self.assertIn("recommended_mode: choose-active-change", ambiguous)
            self.assertIn("REQ-1", ambiguous)
            self.assertIn("REQ-2", ambiguous)

            req1 = self._run_cli(root, "activate", "--change-id", "REQ-1")
            activation = load_yaml(root / ".governance/local/PROJECT_ACTIVATION.yaml")

            self.assertIn("recommended_mode: continue-active-change", req1)
            self.assertIn("active_change_id: REQ-1", req1)
            self.assertIn(".governance/agent-entry.md", req1)
            self.assertEqual(activation["active_change"]["change_id"], "REQ-1")
            self.assertEqual(activation["recommended_mode"], "continue-active-change")

            req2_manifest_path = root / ".governance/changes/REQ-2/manifest.yaml"
            req2_manifest = load_yaml(req2_manifest_path)
            req2_manifest["status"] = "archived"
            write_yaml(req2_manifest_path, req2_manifest)
            upsert_change_entry(root, {
                "change_id": "REQ-2",
                "path": ".governance/changes/REQ-2",
                "status": "archived",
                "current_step": 9,
            })
            archived = self._run_cli(root, "activate", "--change-id", "REQ-2")
            self.assertIn("recommended_mode: change-not-found", archived)

    def test_agent_entry_pack_is_generated_for_target_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "REQ-SKILL", "Skill adoption")

            agent_entry = root / ".governance/agent-entry.md"
            agents = root / ".governance/AGENTS.md"
            current_state = root / ".governance/local/current-state.md"

            self.assertTrue(agent_entry.exists())
            agent_entry_text = agent_entry.read_text(encoding="utf-8")
            self.assertIn("project-scoped, not Agent-scoped", agent_entry_text)
            self.assertIn("project-scoped source of truth", agent_entry_text)
            self.assertIn("ocw resume --change-id <change-id>", agent_entry_text)
            self.assertIn("Do not ask the human to memorize", agent_entry_text)
            self.assertIn(".governance/agent-entry.md", agents.read_text(encoding="utf-8"))
            self.assertIn(".governance/index/active-changes.yaml", current_state.read_text(encoding="utf-8"))

    def test_human_docs_hide_cli_first_burden(self):
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        getting_started = (project_root / "docs/getting-started.md").read_text(encoding="utf-8")
        agent_adoption = (project_root / "docs/agent-adoption.md").read_text(encoding="utf-8")
        docs_map = (project_root / "docs/README.md").read_text(encoding="utf-8")
        agent_skill = (project_root / "docs/agent-skill.md").read_text(encoding="utf-8")
        bootstrap = (project_root / "scripts/bootstrap.sh").read_text(encoding="utf-8")
        quickstart = (project_root / "scripts/quickstart.sh").read_text(encoding="utf-8")

        self.assertNotIn("```bash", readme)
        self.assertEqual(readme.count("ocw "), 0)
        self.assertNotIn("```bash", getting_started)
        self.assertLessEqual(getting_started.count("ocw "), 2)
        self.assertNotIn("```bash", agent_adoption)
        self.assertIn("active-changes.yaml", docs_map)
        self.assertIn("不要让人记 open-cowork CLI", agent_skill)
        self.assertIn("not as a human checklist", bootstrap)
        self.assertNotIn("participants setup", bootstrap)
        self.assertNotIn("step approve", quickstart)
        self.assertIn("个人域单一 Agent 系统", readme)
        self.assertIn("本地个人域多个 Agent 系统调度协同", readme)
        self.assertIn("团队多人域场景", readme)
        self.assertIn("项目级接手规则（Skill）怎么用", readme)
        self.assertIn("open-cowork 的 README 只说明当前框架和流程", readme)
        self.assertIn("核心能力", readme)
        self.assertIn("核心概念", readme)
        self.assertNotIn("当前 `v0.3.5`", readme)
        self.assertNotIn("active changes，并按 open-cowork skill", readme)
        self.assertIn("三类典型落地场景", getting_started)
        self.assertIn("项目级 Agent Entry 使用方式", getting_started)
        self.assertIn("`.governance/agent-entry.md`", readme)
        self.assertNotIn("open-cowork-skill.md", readme)
        self.assertIn("`.governance/` 里放什么", readme)

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

            report = load_yaml(root / ".governance/changes/CHG-V035-FACTS/step-reports/step-1.yaml")

            self.assertEqual(report["intent_summary"]["project_intent"], "Decision facts")
            self.assertIn("src/**", report["intent_summary"]["scope_in"])
            self.assertEqual(report["intent_summary"]["facts_source"], "contract")

    def test_step_reports_fall_back_to_contract_when_intent_scope_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V035-MERGE-FACTS", "--title", "Merge facts")
            self._run_cli(
                root,
                "change",
                "prepare",
                "CHG-V035-MERGE-FACTS",
                "--goal",
                "Decision facts",
                "--scope-in",
                "src/governance/**",
                "--verify-command",
                "python3 -c 'print(\"ok\")'",
            )
            write_yaml(root / ".governance/changes/CHG-V035-MERGE-FACTS/intent-confirmation.yaml", {
                "schema": "intent-confirmation/v1",
                "change_id": "CHG-V035-MERGE-FACTS",
                "status": "confirmed",
                "project_intent": "Decision facts",
                "requirements": [],
                "scope_in": [],
                "scope_out": [],
                "acceptance_criteria": [],
            })

            self._run_cli(root, "step", "report", "--change-id", "CHG-V035-MERGE-FACTS", "--step", "3")
            report = load_yaml(root / ".governance/changes/CHG-V035-MERGE-FACTS/step-reports/step-3.yaml")

            self.assertEqual(report["intent_summary"]["facts_source"], "intent-confirmation")
            self.assertIn("src/governance/**", report["intent_summary"]["scope_in"])
            self.assertIn("contract.scope_in", report["intent_summary"]["merged_from"])
            self.assertIn("contract.verification.checks", report["intent_summary"]["merged_from"])

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
            review_path = root / ".governance/changes/CHG-V035-REVIEW/review.yaml"
            review_payload = load_yaml(review_path)
            review_payload["conditions"] = {"must_before_next_step": [], "followups": ["document release notes"]}
            write_yaml(review_path, review_payload)

            archive_fail = self._run_cli(root, "archive", "--change-id", "CHG-V035-REVIEW", expect=1)
            self.assertIn("Step 8 human gate approval is required", archive_fail)

            self._run_cli(root, "step", "approve", "--change-id", "CHG-V035-REVIEW", "--step", "8", "--approved-by", "human-sponsor")
            self._run_cli(root, "step", "approve", "--change-id", "CHG-V035-REVIEW", "--step", "9", "--approved-by", "human-sponsor")
            archive_ok = self._run_cli(root, "archive", "--change-id", "CHG-V035-REVIEW")
            self.assertIn("Archived change CHG-V035-REVIEW", archive_ok)
            step9 = load_yaml(root / ".governance/archive/CHG-V035-REVIEW/step-reports/step-9.yaml")
            self.assertIn(".governance/archive/CHG-V035-REVIEW/archive-receipt.yaml", step9["artifact_summary"]["archive_preview_files"])
            self.assertIn("document release notes", step9["artifact_summary"]["carry_forward_items"])

    def test_review_invocation_records_heartbeat_and_refreshes_step8_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_verified_change(root, "CHG-V035-REVIEW-HEARTBEAT")

            output = self._run_cli(
                root,
                "review-invocation",
                "--change-id",
                "CHG-V035-REVIEW-HEARTBEAT",
                "--status",
                "started",
                "--reviewer",
                "hermes-agent",
                "--runtime",
                "hermes",
                "--timeout-policy",
                "timeout after 10 minutes; record heartbeat every minute",
                "--note",
                "Hermes review started",
            )
            self.assertIn("Review invocation recorded", output)
            invocation = load_yaml(root / ".governance/changes/CHG-V035-REVIEW-HEARTBEAT/review-invocation.yaml")
            self.assertEqual(invocation["status"], "started")
            self.assertEqual(invocation["events"][0]["note"], "Hermes review started")
            step8 = load_yaml(root / ".governance/changes/CHG-V035-REVIEW-HEARTBEAT/step-reports/step-8.yaml")
            self.assertEqual(step8["artifact_summary"]["review_invocation_status"], "started")
            self.assertIn("timeout after 10 minutes", step8["artifact_summary"]["review_invocation_timeout_policy"])

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
            "05-deterministic-resume-and-merge-safe-governance.md",
            "06-team-adoption-and-context-pack.md",
            "07-v038-runtime-evidence-and-closeout.md",
            "08-v0311-lean-protocol-reset.md",
            "08-v039-team-operating-loop.md",
            "09-v0310-governance-enforcement.md",
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

    def _prepare(self, root: Path, change_id: str, goal: str) -> None:
        self._run_cli(root, "change", "create", change_id, "--title", goal)
        self._run_cli(root, "change", "prepare", change_id, "--goal", goal)

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
        write_yaml(root / f".governance/changes/{change_id}/human-gates.yaml", {
            "schema": "human-gates/v1",
            "change_id": change_id,
            "approvals": {},
        })

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
        write_yaml(change_dir / "human-gates.yaml", {
            "schema": "human-gates/v1",
            "change_id": change_id,
            "approvals": {5: {"status": "approved", "approved_by": "human-sponsor"}},
        })
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": status,
                "current_step": current_step,
            },
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": status,
                "current_step": current_step,
            }],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })


if __name__ == "__main__":
    unittest.main()
