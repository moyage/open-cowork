from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.simple_yaml import load_yaml, write_yaml


class V038RuntimeEvidenceCloseoutTests(unittest.TestCase):
    def test_step_report_has_timing_and_final_round_report_is_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V038-TIME", "Timing closeout")
            intent_path = root / ".governance/changes/CHG-V038-TIME/intent-confirmation.yaml"
            intent = load_yaml(intent_path)
            intent["requirements"] = ["最终报告必须包含初始需求逐项完成对照。"]
            write_yaml(intent_path, intent)
            report = load_yaml(root / ".governance/changes/CHG-V038-TIME/step-reports/step-5.yaml")
            self.assertIn("started_at", report)
            self.assertIn("completed_at", report)
            self.assertIn("duration_seconds", report)

            self._run_cli(root, "run", "--change-id", "CHG-V038-TIME", "--modified", "docs/example.md")
            self._run_cli(root, "verify", "--change-id", "CHG-V038-TIME")
            self._run_cli(root, "review", "--change-id", "CHG-V038-TIME", "--decision", "approve", "--reviewer", "independent-reviewer")
            self._run_cli(root, "step", "approve", "--change-id", "CHG-V038-TIME", "--step", "8", "--approved-by", "human-sponsor")
            self._run_cli(root, "step", "approve", "--change-id", "CHG-V038-TIME", "--step", "9", "--approved-by", "human-sponsor")
            self._run_cli(root, "archive", "--change-id", "CHG-V038-TIME")

            archive = root / ".governance/archive/CHG-V038-TIME"
            self.assertTrue((archive / "FINAL_ROUND_REPORT.md").exists())
            final_report = (archive / "FINAL_ROUND_REPORT.md").read_text(encoding="utf-8")
            self.assertIn("# 最终闭环报告", final_report)
            self.assertIn("## 本轮完成概览", final_report)
            self.assertIn("## 初始需求逐项完成对照", final_report)
            self.assertIn("## 四阶段九步过程简报", final_report)
            self.assertIn("## 复盘总结", final_report)
            self.assertIn("第一阶段：定义与对齐", final_report)
            self.assertIn("完成状态：已完成", final_report)
            self.assertIn("本步完成：", final_report)
            self.assertIn("归档前暴露出最终报告质量不足的问题", final_report)
            self.assertNotIn("# FINAL_ROUND_REPORT", final_report)
            self.assertNotIn("Phase 1", final_report)
            self.assertNotIn("status:", final_report)
            self.assertNotIn("inputs:", final_report)
            self.assertNotIn("outputs:", final_report)
            self.assertNotIn("duration_seconds", final_report)
            self.assertNotIn("revision-open", final_report)
            self.assertNotIn("Hard-blocked", final_report)
            self.assertNotIn("Hermes independent review requested changes", final_report)
            self.assertNotIn("context pack", final_report)
            self.assertNotIn("compact handoff", final_report)
            receipt = load_yaml(archive / "archive-receipt.yaml")
            snapshot = load_yaml(archive / "FINAL_STATUS_SNAPSHOT.yaml")
            self.assertIn("FINAL_ROUND_REPORT.md", receipt["traceability"]["final_round_report"])
            self.assertIn("FINAL_ROUND_REPORT.md", snapshot["refs"]["final_round_report"])
            self.assertIn("context-pack.yaml", receipt["traceability"]["context_pack"])
            self.assertIn("handoff-compact.md", snapshot["refs"]["compact_handoff"])

    def test_runtime_profiles_adapter_validation_events_and_evidence_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V038-RUNTIME", "Runtime evidence")
            self._run_cli(
                root,
                "runtime",
                "profile",
                "add",
                "--runtime-id",
                "local-codex",
                "--runtime-type",
                "local-cli",
                "--owner",
                "executor-agent",
                "--capability",
                "run-command",
                "--risk",
                "shell-access",
                "--evidence",
                "command-output",
            )
            profile = load_yaml(root / ".governance/runtime-profiles/local-codex.yaml")
            self.assertEqual(profile["authority"], "capability_description_only")

            self._run_cli(root, "runtime-event", "append", "--change-id", "CHG-V038-RUNTIME", "--event-type", "command_completed", "--step", "6")
            self.assertTrue((root / ".governance/changes/CHG-V038-RUNTIME/evidence/runtime-events/events.yaml").exists())

            self._run_cli(root, "run", "--change-id", "CHG-V038-RUNTIME", "--modified", "docs/runtime.md", "--test-output", "ok")
            adapter_output = root / ".governance/changes/CHG-V038-RUNTIME/evidence/adapter-output.yaml"
            self._run_cli(root, "adapter", "validate-output", str(adapter_output))
            self._run_cli(root, "evidence", "append", "--change-id", "CHG-V038-RUNTIME", "--adapter", str(adapter_output))
            self._run_cli(root, "evidence", "index", "--change-id", "CHG-V038-RUNTIME")
            index = load_yaml(root / ".governance/changes/CHG-V038-RUNTIME/evidence/index.yaml")
            kinds = {item["kind"] for item in index["entries"]}
            self.assertIn("adapter_output", kinds)
            self.assertIn("runtime_event", kinds)
            self._run_cli(root, "verify", "--change-id", "CHG-V038-RUNTIME")
            self._run_cli(root, "review", "--change-id", "CHG-V038-RUNTIME", "--decision", "approve", "--reviewer", "independent-reviewer")
            review = load_yaml(root / ".governance/changes/CHG-V038-RUNTIME/review.yaml")
            self.assertEqual(review["runtime_evidence_sources"]["conflict_policy"], "governance_facts_override_runtime_events")
            self.assertEqual(review["runtime_evidence_sources"]["conflict_status"], "not_detected")
            self.assertTrue(review["runtime_evidence_sources"]["sources"])

    def test_reviewer_cannot_be_step6_executor_even_with_mismatch_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V038-SELF-REVIEW", "No self review")
            self._run_cli(root, "run", "--change-id", "CHG-V038-SELF-REVIEW", "--modified", "docs/self-review.md")
            self._run_cli(root, "verify", "--change-id", "CHG-V038-SELF-REVIEW")
            output = self._run_cli(
                root,
                "review",
                "--change-id",
                "CHG-V038-SELF-REVIEW",
                "--decision",
                "approve",
                "--reviewer",
                "executor-agent",
                "--allow-reviewer-mismatch",
                "--bypass-reason",
                "try bypass",
                "--bypass-recorded-by",
                "human-sponsor",
                "--bypass-evidence-ref",
                "manual",
                expect=1,
            )
            self.assertIn("reviewer must be independent from Step 6 executor", output)

    def test_context_pack_levels_source_index_checkpoint_preview_and_handoff_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V038-CONTEXT", "Context completeness")
            manifest_path = root / ".governance/changes/CHG-V038-CONTEXT/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest["source_docs"] = ["docs/source-a.md", "docs/source-b.md"]
            write_yaml(manifest_path, manifest)

            minimal = json.loads(self._run_cli(root, "context-pack", "read", "--change-id", "CHG-V038-CONTEXT", "--level", "minimal", "--format", "json"))
            standard = json.loads(self._run_cli(root, "context-pack", "read", "--change-id", "CHG-V038-CONTEXT", "--level", "standard", "--format", "json"))
            deep = json.loads(self._run_cli(root, "context-pack", "read", "--change-id", "CHG-V038-CONTEXT", "--level", "deep", "--format", "json"))
            self.assertEqual(minimal["supporting_reads"], [])
            self.assertGreater(len(standard["supporting_reads"]), 0)
            self.assertEqual(standard["optional_deep_reads"], [])
            self.assertEqual(deep["optional_deep_reads"], ["docs/source-a.md", "docs/source-b.md"])
            self.assertTrue((root / ".governance/changes/CHG-V038-CONTEXT/context/source-index.yaml").exists())
            self.assertTrue((root / ".governance/changes/CHG-V038-CONTEXT/context/compression-checkpoint.md").exists())

            preview = self._run_cli(root, "profile", "apply", "team-standard", "--preview")
            self.assertIn("Profile apply preview", preview)
            self._run_cli(root, "profile", "apply", "team-standard")
            self._run_cli(root, "handoff", "--compact", "--change-id", "CHG-V038-CONTEXT")
            handoff_lines = (root / ".governance/changes/CHG-V038-CONTEXT/context/handoff-compact.md").read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(handoff_lines), 120)

    def test_full_implementation_gate_blocks_unapproved_unchecked_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V038-FULL", "Full implementation")
            contract_path = root / ".governance/changes/CHG-V038-FULL/contract.yaml"
            contract = load_yaml(contract_path)
            contract.setdefault("forbidden_actions", []).append("downgrade_or_partial_implementation_without_human_approval")
            write_yaml(contract_path, contract)
            (root / ".governance/changes/CHG-V038-FULL/tasks.md").write_text("- [ ] Required complete task\n", encoding="utf-8")
            self._run_cli(root, "run", "--change-id", "CHG-V038-FULL", "--modified", "docs/full.md")
            output = self._run_cli(root, "verify", "--change-id", "CHG-V038-FULL")
            self.assertIn("-> blocker", output)
            verify = load_yaml(root / ".governance/changes/CHG-V038-FULL/verify.yaml")
            self.assertIn("unapproved incomplete task - Required complete task", verify["issues"])

    def _prepare(self, root: Path, change_id: str, goal: str) -> None:
        self._run_cli(root, "change", "create", change_id, "--title", goal)
        self._run_cli(
            root,
            "change",
            "prepare",
            change_id,
            "--goal",
            goal,
            "--scope-in",
            "docs/**",
            "--verify-command",
            "python3 -c 'print(\"ok\")'",
            "--active-policy",
            "force",
        )
        self._run_cli(root, "intent", "confirm", "--change-id", change_id, "--confirmed-by", "human-sponsor")
        self._run_cli(root, "step", "approve", "--change-id", change_id, "--step", "2", "--approved-by", "human-sponsor")
        self._run_cli(root, "step", "approve", "--change-id", change_id, "--step", "3", "--approved-by", "human-sponsor")
        self._run_cli(root, "step", "approve", "--change-id", change_id, "--step", "4", "--approved-by", "human-sponsor")
        self._run_cli(root, "step", "approve", "--change-id", change_id, "--step", "5", "--approved-by", "human-sponsor")

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
