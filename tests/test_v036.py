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


class V036DeterministicResumeTests(unittest.TestCase):
    def test_resume_is_deterministic_for_missing_idle_single_and_multi_change_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            missing.mkdir()
            missing_output = self._run_cli(missing, "resume")
            self.assertIn("recommended_mode: install-or-initialize", missing_output)
            self.assertIn("protocol_trigger: command", missing_output)

            idle = Path(tmp) / "idle"
            idle.mkdir()
            self._run_cli(idle, "init")
            idle_output = self._run_cli(idle, "resume")
            self.assertIn("recommended_mode: open-new-change", idle_output)
            self.assertTrue((idle / ".governance/.gitignore").exists())

            project = Path(tmp) / "project"
            project.mkdir()
            self._run_cli(project, "init")
            self._prepare(project, "REQ-1", "需求 1")
            single_output = self._run_cli(project, "resume")
            self.assertIn("recommended_mode: continue-active-change", single_output)
            self.assertIn("active_change_id: REQ-1", single_output)
            self.assertTrue((project / ".governance/local/PROJECT_ACTIVATION.yaml").exists())
            self.assertTrue((project / ".governance/local/current-state.md").exists())
            self.assertFalse((project / ".governance/PROJECT_ACTIVATION.yaml").exists())

            self._prepare(project, "REQ-2", "需求 2")
            multi_output = self._run_cli(project, "resume", "--list")
            self.assertIn("recommended_mode: choose-active-change", multi_output)
            self.assertIn("REQ-1", multi_output)
            self.assertIn("REQ-2", multi_output)

            req2_json = self._run_cli(project, "resume", "--change-id", "REQ-2", "--format", "json")
            payload = json.loads(req2_json)
            self.assertEqual(payload["recommended_mode"], "continue-active-change")
            self.assertEqual(payload["active_change"]["change_id"], "REQ-2")
            self.assertIn(".governance/local/current-state.md", payload["recommended_read_set"])

    def test_generated_agent_entry_is_generic_and_local_projection_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "REQ-GENERIC", "Generic entry")

            agent_entry = (root / ".governance/agent-entry.md").read_text(encoding="utf-8")
            agents = (root / ".governance/AGENTS.md").read_text(encoding="utf-8")
            playbook = (root / ".governance/agent-playbook.md").read_text(encoding="utf-8")
            ignore = (root / ".governance/.gitignore").read_text(encoding="utf-8")

            self.assertIn("ocw resume", agent_entry)
            self.assertIn("protocol trigger", agent_entry)
            self.assertIn(".governance/local/**", agent_entry)
            self.assertNotIn("REQ-GENERIC", agent_entry)
            self.assertNotIn("REQ-GENERIC", agents)
            self.assertNotIn("REQ-GENERIC", playbook)
            self.assertIn("/local/", ignore)
            self.assertIn("/PROJECT_ACTIVATION.yaml", ignore)
            self.assertIn("/current-state.md", ignore)
            self.assertIn("/runtime/status/", ignore)

    def test_index_rebuild_restores_indexes_from_authoritative_change_and_archive_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "REQ-ACTIVE", "Active work")
            self._write_archived_change(root, "REQ-ARCHIVED")

            write_yaml(root / ".governance/index/active-changes.yaml", {"schema": "active-changes/v1", "changes": []})
            write_yaml(root / ".governance/index/changes-index.yaml", {"schema": "changes-index/v1", "changes": []})
            write_yaml(root / ".governance/index/archive-map.yaml", {"schema": "archive-map/v1", "archives": []})

            output = self._run_cli(root, "index", "rebuild")
            self.assertIn("Index rebuilt", output)

            active = load_yaml(root / ".governance/index/active-changes.yaml")
            changes = load_yaml(root / ".governance/index/changes-index.yaml")
            archive_map = load_yaml(root / ".governance/index/archive-map.yaml")

            self.assertEqual([item["change_id"] for item in active["changes"]], ["REQ-ACTIVE"])
            self.assertEqual([item["change_id"] for item in changes["changes"]], ["REQ-ACTIVE", "REQ-ARCHIVED"])
            self.assertEqual(archive_map["archives"][0]["change_id"], "REQ-ARCHIVED")
            self.assertEqual(archive_map["archives"][0]["receipt"], ".governance/archive/REQ-ARCHIVED/archive-receipt.yaml")

    def _prepare(self, root: Path, change_id: str, goal: str) -> None:
        self._run_cli(root, "change", "create", change_id, "--title", goal)
        self._run_cli(root, "change", "prepare", change_id, "--goal", goal, "--active-policy", "force")

    def _write_archived_change(self, root: Path, change_id: str) -> None:
        archive_dir = root / ".governance/archive" / change_id
        archive_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(archive_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": "Archived work",
            "status": "archived",
            "current_step": 9,
        })
        write_yaml(archive_dir / "archive-receipt.yaml", {
            "schema": "archive-receipt/v1",
            "change_id": change_id,
            "archive_executed": True,
            "archived_at": "2026-04-27T00:00:00+00:00",
        })

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
