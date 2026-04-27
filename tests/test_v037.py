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


class V037TeamAdoptionContextPackTests(unittest.TestCase):
    def test_profile_list_show_and_apply_write_fixed_adoption_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")

            list_output = self._run_cli(root, "profile", "list")
            self.assertIn("core", list_output)
            self.assertIn("team-standard", list_output)
            self.assertIn("large-reference-set", list_output)
            self.assertIn("可叠加，不是单独协作档位", list_output)

            show_payload = json.loads(self._run_cli(root, "profile", "show", "team-standard", "--format", "json"))
            self.assertEqual(show_payload["profile_id"], "team-standard")
            self.assertEqual(show_payload["human_label"], "团队标准协作")
            self.assertIn("compact_handoff", show_payload["enabled_controls"])

            apply_output = self._run_cli(root, "profile", "apply", "team-standard")
            self.assertIn("Applied adoption profile: team-standard", apply_output)
            adoption = load_yaml(root / ".governance/profiles/adoption.yaml")
            self.assertEqual(adoption["profile_id"], "team-standard")
            self.assertEqual(adoption["profile_version"], "ocw.adoption-profile.v1")
            self.assertIn("executor_final_self_review", adoption["prohibited"])
            self.assertTrue((root / ".governance/participants/current-agent.yaml").exists())
            self.assertFalse((root / ".governance/participants/codex-agent.yaml").exists())

            self._run_cli(root, "profile", "apply", "team-standard", "--agent-id", "hermes-agent")
            self.assertTrue((root / ".governance/participants/hermes-agent.yaml").exists())

    def test_context_pack_create_and_handoff_reference_authoritative_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-V037", "Context pack behavior")

            create_output = self._run_cli(root, "context-pack", "create", "--change-id", "CHG-V037")
            self.assertIn("Context pack created", create_output)

            context_dir = root / ".governance/changes/CHG-V037/context"
            pack = load_yaml(context_dir / "context-pack.yaml")
            self.assertEqual(pack["context_pack_version"], "ocw.context-pack.v1")
            self.assertEqual(pack["change_id"], "CHG-V037")
            self.assertIn(".governance/changes/CHG-V037/contract.yaml", pack["authoritative_reads"])
            self.assertIn(".governance/changes/CHG-V037/bindings.yaml", pack["authoritative_reads"])
            self.assertNotIn(".governance/archive/CHG-V037", "\n".join(pack["authoritative_reads"]))
            self.assertTrue((context_dir / "context-pack.md").exists())

            handoff_output = self._run_cli(root, "handoff", "--compact", "--change-id", "CHG-V037")
            self.assertIn("Compact handoff written", handoff_output)
            handoff = (context_dir / "handoff-compact.md").read_text(encoding="utf-8")
            self.assertIn("Recommended Read Set", handoff)
            self.assertIn(".governance/changes/CHG-V037/context/context-pack.yaml", handoff)
            self.assertIn(".governance/changes/CHG-V037/context/handoff-compact.md", handoff)
            self.assertIn("Context pack points to authoritative facts", handoff)

            manifest_path = root / ".governance/changes/CHG-V037/manifest.yaml"
            manifest = load_yaml(manifest_path)
            manifest["status"] = "step7-blocked"
            manifest["current_step"] = 7
            write_yaml(manifest_path, manifest)
            write_yaml(root / ".governance/changes/CHG-V037/verify.yaml", {
                "summary": {"status": "blocker", "blocker_count": 1},
            })
            self._run_cli(root, "context-pack", "create", "--change-id", "CHG-V037")
            blocked_pack = load_yaml(context_dir / "context-pack.yaml")
            self.assertTrue(blocked_pack["summary"]["blocked"])

    def test_resume_prefers_context_pack_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._prepare(root, "CHG-RESUME", "Resume with context pack")
            self._run_cli(root, "context-pack", "create", "--change-id", "CHG-RESUME")
            self._run_cli(root, "handoff", "--compact", "--change-id", "CHG-RESUME")

            payload = json.loads(self._run_cli(root, "resume", "--change-id", "CHG-RESUME", "--format", "json"))

            read_set = payload["recommended_read_set"]
            self.assertLess(
                read_set.index(".governance/changes/CHG-RESUME/context/context-pack.yaml"),
                read_set.index(".governance/changes/CHG-RESUME/contract.yaml"),
            )
            self.assertIn(".governance/changes/CHG-RESUME/context/handoff-compact.md", read_set)
            self.assertIn("Context pack is a pointer to authoritative governance facts.", payload["agent_instructions"])

    def _prepare(self, root: Path, change_id: str, goal: str) -> None:
        self._run_cli(root, "change", "create", change_id, "--title", goal)
        self._run_cli(root, "change", "prepare", change_id, "--goal", goal, "--active-policy", "force")

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
