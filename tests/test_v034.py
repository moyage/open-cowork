from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.simple_yaml import load_yaml
from governance.step_matrix import STEP_LABELS


class V034HumanOnboardingTests(unittest.TestCase):
    def test_step_labels_are_human_named_and_status_uses_them(self):
        self.assertEqual(STEP_LABELS[1], "明确意图 / Clarify intent")
        self.assertEqual(STEP_LABELS[4], "组装变更包 / Assemble change package")
        self.assertEqual(STEP_LABELS[5], "批准开工 / Approve execution")
        self.assertEqual(STEP_LABELS[8], "独立审查 / Independent review")
        self.assertEqual(STEP_LABELS[9], "归档接续 / Archive and handoff")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V034-LABELS", "--title", "Readable steps")
            self._run_cli(root, "change", "prepare", "CHG-V034-LABELS", "--goal", "Readable step names")

            output = self._run_cli(root, "status")

            self.assertIn("Step 1: 明确意图 / Clarify intent", output)
            self.assertIn("next_decision: Step 2 / 确定范围 / Lock scope", output)
            self.assertIn("project_summary: Readable step names", output)
            self.assertNotIn("Clarify the goal", output)
            self.assertNotIn("Approve the start", output)

    def test_project_activation_reports_project_scoped_handoff_for_any_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V034-ACTIVATE", "--title", "Activation")
            self._run_cli(root, "change", "prepare", "CHG-V034-ACTIVATE", "--goal", "Cross-agent activation")

            output = self._run_cli(root, "activate")
            activation = load_yaml(root / ".governance/local/PROJECT_ACTIVATION.yaml")

            self.assertIn("open-cowork project activation", output)
            self.assertIn("project_scope: project-level", output)
            self.assertIn("active_change_id: CHG-V034-ACTIVATE", output)
            self.assertIn("current_step: 1", output)
            self.assertIn(".governance/AGENTS.md", output)
            self.assertIn(".governance/local/current-state.md", output)
            self.assertIn(".governance/changes/CHG-V034-ACTIVATE/contract.yaml", output)
            self.assertIn("continue the active change; do not reinstall", output)
            self.assertEqual(activation["project_scope"], "project-level")
            self.assertEqual(activation["active_change"]["change_id"], "CHG-V034-ACTIVATE")
            self.assertEqual(activation["recommended_mode"], "continue-active-change")

    def test_human_docs_are_indexed_and_hide_cli_first_burden(self):
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        docs_map = (project_root / "docs/README.md").read_text(encoding="utf-8")
        glossary = (project_root / "docs/glossary.md").read_text(encoding="utf-8")
        specs_readme = (project_root / "docs/specs/README.md").read_text(encoding="utf-8")
        archive_readme = (project_root / "docs/archive/README.md").read_text(encoding="utf-8")

        self.assertIn("人只需要对 Agent 说", readme)
        self.assertIn("CLI 是 Agent 内部工具", readme)
        self.assertIn("flowchart TD", readme)
        self.assertIn("activate 后接续", readme)
        self.assertLess(readme.count("ocw "), 12)

        self.assertIn("普通读者先看", docs_map)
        self.assertIn("Agent 执行面", docs_map)
        self.assertIn("历史证据，不是当前实施入口", docs_map)

        for term in [
            "Contract",
            "Evidence",
            "Bindings",
            "Continuity",
            "变更包",
            "Closeout",
            "Gate",
            "Increment",
            "Digest",
        ]:
            self.assertIn(term, glossary)

        self.assertIn("当前有效规格", specs_readme)
        self.assertIn("不是试用过程记录", specs_readme)
        self.assertIn("历史证据，不是当前实施入口", archive_readme)

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
