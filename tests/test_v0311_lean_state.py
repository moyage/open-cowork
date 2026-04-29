from __future__ import annotations

import tempfile
import unittest
import contextlib
import io
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.lean_paths import (
    LEAN_LAYOUT_FILES,
    LEGACY_HEAVY_DIRS,
    default_read_set_paths,
    ensure_lean_layout,
)
from governance.lean_state import (
    PHASES,
    REVIEW_DECISIONS,
    REVIEW_STATUSES,
    initial_lean_state,
    load_lean_state,
    validate_lean_documents,
    validate_lean_state,
)
from governance.simple_yaml import load_yaml, write_yaml


class V0311LeanStateTests(unittest.TestCase):
    def test_default_read_set_is_fixed_and_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            paths = default_read_set_paths(root)

            self.assertEqual([path.name for path in paths], [
                "AGENTS.md",
                "agent-entry.md",
                "current-state.md",
                "state.yaml",
            ])
            self.assertNotIn("ledger.yaml", [path.name for path in paths])
            self.assertNotIn("evidence.yaml", [path.name for path in paths])
            self.assertNotIn("rules.yaml", [path.name for path in paths])

    def test_lean_layout_initialization_does_not_create_legacy_heavy_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            ensure_lean_layout(root)

            for filename in LEAN_LAYOUT_FILES:
                self.assertTrue((root / ".governance" / filename).exists(), filename)
            self.assertTrue((root / ".governance/templates").is_dir())
            for dirname in LEGACY_HEAVY_DIRS:
                self.assertFalse((root / ".governance" / dirname).exists(), dirname)

    def test_initial_state_contains_v0311_required_schema_fields(self):
        state = initial_lean_state(round_id="R-TEST-001", goal="精简治理状态")
        active_round = state["active_round"]
        participant_init = active_round["participant_initialization"]

        self.assertEqual(state["protocol"]["version"], "0.3.11")
        self.assertEqual(active_round["phase"], "intent-scope")
        self.assertIn(active_round["phase"], PHASES)
        self.assertIn("plan", active_round)
        self.assertIn("verification_plan", active_round)
        self.assertEqual(participant_init["role_bindings"][0]["role"], "owner_agent")
        self.assertIn("authority_scope", participant_init["role_bindings"][0])
        self.assertIn("output_responsibility", participant_init["role_bindings"][0])
        self.assertIn("approval_evidence_ref", participant_init["bypass"])
        self.assertEqual(active_round["review"]["status"], "not-requested")
        self.assertIn(active_round["review"]["status"], REVIEW_STATUSES)
        self.assertEqual(active_round["review"]["decision"], "")
        self.assertIn("decision_needed", state)
        self.assertEqual(validate_lean_state(state), [])

    def test_validation_rejects_illegal_review_status_decision_combo(self):
        state = initial_lean_state(round_id="R-TEST-001", goal="非法 review 矩阵")
        state["active_round"]["review"]["status"] = "completed"
        state["active_round"]["review"]["decision"] = ""

        errors = validate_lean_state(state)

        self.assertIn("review decision is required when review status is completed", errors)
        self.assertIn("approve", REVIEW_DECISIONS)

    def test_load_lean_state_reads_authoritative_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root, initial_state=initial_lean_state(round_id="R-LOAD-001", goal="读取权威状态"))

            loaded = load_lean_state(root)

            self.assertEqual(loaded["active_round"]["round_id"], "R-LOAD-001")
            self.assertEqual(validate_lean_state(loaded), [])

    def test_cli_init_defaults_to_lean_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            exit_code = main(["--root", str(root), "init"])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / ".governance/state.yaml").exists())
            self.assertTrue((root / ".governance/agent-entry.md").exists())
            self.assertFalse((root / ".governance/index").exists())
            self.assertFalse((root / ".governance/changes").exists())

    def test_cli_onboard_defaults_to_lean_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            exit_code = main([
                "--root",
                str(root),
                "onboard",
                "--target",
                str(root),
                "--yes",
                "--no-diagnose",
            ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / ".governance/state.yaml").exists())
            self.assertTrue((root / ".governance/current-state.md").exists())
            self.assertFalse((root / ".governance/index").exists())
            self.assertFalse((root / ".governance/changes").exists())

    def test_cli_status_reads_lean_state_without_legacy_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["--root", str(root), "init"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "status"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("# open-cowork lean status", output)
            self.assertIn("- layout: lean", output)
            self.assertIn("- phase: intent-scope", output)
            self.assertNotIn("Status check failed", output)

    def test_cli_resume_reads_lean_state_without_legacy_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root, initial_state=initial_lean_state(
                round_id="R-LEAN-RESUME",
                goal="从 lean state 接续",
            ))

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "resume"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("- recommended_mode: continue-active-round", output)
            self.assertIn("- active_round_id: R-LEAN-RESUME", output)
            self.assertIn(".governance/state.yaml", output)
            self.assertFalse((root / ".governance/index").exists())

    def test_cli_resume_surfaces_compact_resilience_rules_for_lean_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root, initial_state=initial_lean_state(
                round_id="R-COMPACT",
                goal="降低上下文压力",
            ))

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "resume"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Context discipline:", output)
            self.assertIn("Do not full-scan cold history", output)
            self.assertIn("Write large outputs to files and cite evidence refs", output)

    def test_cli_status_surfaces_context_budget_for_lean_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "status"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("## Context Budget", output)
            self.assertIn("- default_read_set: bounded", output)
            self.assertIn("- large_outputs: write-to-file-and-reference", output)

    def test_initialized_state_and_current_state_stay_within_context_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            ensure_lean_layout(root)

            state_lines = (root / ".governance/state.yaml").read_text(encoding="utf-8").splitlines()
            current_state_lines = (root / ".governance/current-state.md").read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(state_lines), 400)
            self.assertLessEqual(len(current_state_lines), 200)

    def test_validation_covers_ledger_evidence_and_rules_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root)

            errors = validate_lean_documents(root)

            self.assertEqual(errors, [])

    def test_validation_rejects_invalid_rule_failure_impact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_lean_layout(root)
            (root / ".governance/rules.yaml").write_text(
                "- id: lint\n"
                "  failure_impact: fatal\n",
                encoding="utf-8",
            )

            errors = validate_lean_documents(root)

            self.assertIn("rules.yaml item 0 failure_impact is invalid", errors)

    def test_cli_round_rule_and_evidence_commands_update_lean_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "round",
                "start",
                "--round-id",
                "R-CLI-001",
                "--goal",
                "收口 lean 命令",
                "--scope-in",
                "src/governance/**",
                "--scope-out",
                "legacy heavy dirs",
                "--acceptance",
                "命令可写入 lean 文件",
            ]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "round",
                "participants",
                "init",
                "--sponsor",
                "human:mlabs",
                "--owner-agent",
                "codex",
                "--executor",
                "codex",
                "--reviewer",
                "hermes",
            ]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "round",
                "approve",
                "--gate",
                "execution",
                "--approved-by",
                "human:mlabs",
                "--evidence-ref",
                "E-APPROVAL-001",
            ]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "evidence",
                "add",
                "--id",
                "E-CLI-001",
                "--kind",
                "test",
                "--ref",
                "tests/test_v0311_lean_state.py",
                "--summary",
                "命令测试",
                "--created-by",
                "codex",
            ]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "rule",
                "add",
                "--id",
                "review-lint",
                "--name",
                "review lint",
                "--kind",
                "lint",
                "--failure-impact",
                "warning",
                "--applies-to",
                "closeout",
            ]), 0)

            state = load_yaml(root / ".governance/state.yaml")
            evidence = load_yaml(root / ".governance/evidence.yaml")
            rules = load_yaml(root / ".governance/rules.yaml")
            self.assertEqual(state["active_round"]["round_id"], "R-CLI-001")
            self.assertEqual(state["active_round"]["participant_initialization"]["status"], "complete")
            self.assertEqual(state["active_round"]["gates"]["execution"]["status"], "approved")
            self.assertIn("E-CLI-001", state["active_round"]["evidence_refs"])
            self.assertEqual(evidence[0]["evidence_id"], "E-CLI-001")
            self.assertEqual(rules[0]["id"], "review-lint")
            self.assertEqual(state["active_round"]["external_rules"]["active"][0]["id"], "review-lint")
            self.assertFalse((root / ".governance/index").exists())
            self.assertFalse((root / ".governance/changes").exists())

    def test_cli_blocking_rule_change_requires_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.assertEqual(main(["--root", str(root), "init"]), 0)
            blocked = main([
                "--root",
                str(root),
                "rule",
                "add",
                "--id",
                "release-review",
                "--name",
                "release review",
                "--kind",
                "review",
                "--failure-impact",
                "blocking",
                "--applies-to",
                "closeout",
            ])
            self.assertEqual(blocked, 1)
            self.assertEqual(load_yaml(root / ".governance/rules.yaml"), [])

            approved = main([
                "--root",
                str(root),
                "rule",
                "add",
                "--id",
                "release-review",
                "--name",
                "release review",
                "--kind",
                "review",
                "--failure-impact",
                "blocking",
                "--applies-to",
                "closeout",
                "--authorization-ref",
                "E-HUMAN-AUTH-001",
            ])
            self.assertEqual(approved, 0)
            self.assertEqual(load_yaml(root / ".governance/rules.yaml")[0]["id"], "release-review")

    def test_cli_round_close_requires_closeout_gate_and_writes_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertEqual(main([
                "--root",
                str(root),
                "round",
                "start",
                "--round-id",
                "R-CLOSE-001",
                "--goal",
                "发布前收口",
            ]), 0)
            blocked = main([
                "--root",
                str(root),
                "round",
                "close",
                "--closed-by",
                "codex",
            ])
            self.assertEqual(blocked, 1)

            state = load_yaml(root / ".governance/state.yaml")
            active_round = state["active_round"]
            active_round["participants"].update({
                "sponsor": "human:mlabs",
                "owner_agent": "codex",
                "executor": "codex",
                "reviewer": "hermes",
            })
            active_round["participant_initialization"]["status"] = "complete"
            active_round["participant_initialization"]["initialized_roles"] = [
                "sponsor",
                "owner_agent",
                "executor",
                "reviewer",
            ]
            active_round["participant_initialization"]["missing_roles"] = []
            active_round["gates"]["execution"]["status"] = "approved"
            active_round["gates"]["execution"]["approval_evidence_ref"] = "E-EXEC-001"
            active_round["verify"]["status"] = "pass"
            active_round["review"]["status"] = "completed"
            active_round["review"]["decision"] = "approve"
            active_round["review"]["reviewer"] = "hermes"
            active_round["gates"]["closeout"]["status"] = "approved"
            active_round["gates"]["closeout"]["approval_evidence_ref"] = "E-CLOSE-001"
            write_yaml(root / ".governance/state.yaml", state)

            closed = main([
                "--root",
                str(root),
                "round",
                "close",
                "--closed-by",
                "codex",
                "--evidence-ref",
                "E-CLOSE-001",
                "--summary",
                "全部发布前检查完成",
            ])

            self.assertEqual(closed, 0)
            ledger = load_yaml(root / ".governance/ledger.yaml")
            state = load_yaml(root / ".governance/state.yaml")
            self.assertEqual(ledger[0]["round_id"], "R-CLOSE-001")
            self.assertEqual(ledger[0]["final_status"], "completed")
            self.assertEqual(ledger[0]["closeout_summary"], "全部发布前检查完成")
            self.assertEqual(state["active_round"]["phase"], "closeout")
            self.assertEqual(validate_lean_documents(root), [])

            duplicate = main([
                "--root",
                str(root),
                "round",
                "close",
                "--closed-by",
                "codex",
            ])
            self.assertEqual(duplicate, 1)
            self.assertEqual(len(load_yaml(root / ".governance/ledger.yaml")), 1)


if __name__ == "__main__":
    unittest.main()
