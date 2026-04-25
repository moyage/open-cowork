from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index, read_changes_index, read_current_change, set_current_change, upsert_change_entry
from governance.simple_yaml import load_yaml, write_yaml


class CliTests(unittest.TestCase):
    def test_contract_validate_writes_pass_and_fail_timeline_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-CONTRACT",
                    "--title",
                    "Contract events",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-CONTRACT"
            contract_path = change_dir / "contract.yaml"
            write_yaml(contract_path, {
                "objective": "contract-pass",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["ContractSchema"],
                "verification": {"commands": ["python3 -m unittest"], "checks": ["contract-valid"]},
                "evidence_expectations": {"required": ["contract.yaml"]},
            })

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-CLI-CONTRACT"])
            self.assertEqual(exit_code, 0)

            month_file = root / ".governance/runtime/timeline" / f"events-{__import__('datetime').datetime.utcnow().strftime('%Y%m')}.yaml"
            payload = load_yaml(month_file)
            self.assertTrue(any(
                event["change_id"] == "CHG-CLI-CONTRACT" and event["event_type"] == "contract_validate_pass"
                for event in payload["events"]
            ))

            write_yaml(contract_path, {
                "objective": "",
                "scope_in": [".governance/**"],
            })
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-CLI-CONTRACT"])
            self.assertEqual(exit_code, 1)

            payload = load_yaml(month_file)
            self.assertTrue(any(
                event["change_id"] == "CHG-CLI-CONTRACT" and event["event_type"] == "contract_validate_fail"
                for event in payload["events"]
            ))
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-CLI-CONTRACT"])
            self.assertEqual(exit_code, 1)

            payload = load_yaml(month_file)
            fail_events = [
                event for event in payload["events"]
                if event["change_id"] == "CHG-CLI-CONTRACT" and event["event_type"] == "contract_validate_fail"
            ]
            self.assertEqual(len(fail_events), 2)

    def test_change_create_sets_active_change_and_index_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-1",
                    "--title",
                    "CLI change package",
                ])

            self.assertEqual(exit_code, 0)
            current_change = read_current_change(root)
            changes_index = read_changes_index(root)
            manifest = load_yaml(root / ".governance/changes/CHG-CLI-1/manifest.yaml")

            self.assertEqual(current_change["current_change_id"], "CHG-CLI-1")
            self.assertEqual(current_change["status"], "drafting")
            self.assertEqual(manifest["title"], "CLI change package")
            self.assertEqual(changes_index["changes"][0]["change_id"], "CHG-CLI-1")
            self.assertIn("Created change package CHG-CLI-1", stdout.getvalue())

    def test_change_prepare_fills_main_chain_files_and_valid_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-PREPARE", "--title", "Prepare pilot"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-PREPARE",
                    "--goal",
                    "Use open-cowork to govern a first personal domain change",
                    "--scope-in",
                    "src/**",
                    "--scope-in",
                    "tests/**",
                    "--verify-command",
                    "python3 -m unittest discover -s tests",
                    "--profile",
                    "personal",
                ])

            output = stdout.getvalue()
            change_dir = root / ".governance/changes/CHG-PREPARE"
            self.assertEqual(exit_code, 0)
            self.assertIn("Change prepared: CHG-PREPARE", output)
            self.assertIn("Agent-first handoff ready", output)
            self.assertIn(".governance/current-state.md", output)
            self.assertNotIn("personal domain Agent prompt", output)
            self.assertIn("Use open-cowork", (change_dir / "intent.md").read_text(encoding="utf-8"))
            self.assertIn("src/**", (change_dir / "requirements.md").read_text(encoding="utf-8"))
            self.assertIn("Step 6", (change_dir / "tasks.md").read_text(encoding="utf-8"))

            contract = load_yaml(change_dir / "contract.yaml")
            bindings = load_yaml(change_dir / "bindings.yaml")
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertEqual(contract["change_id"], "CHG-PREPARE")
            self.assertIn(".governance/changes/CHG-PREPARE/evidence/**", contract["scope_in"])
            self.assertEqual(contract["verification"]["commands"], ["python3 -m unittest discover -s tests"])
            self.assertIn("no_executor_reviewer_merge", contract["forbidden_actions"])
            self.assertEqual(bindings["profile"], "personal")
            self.assertEqual(bindings["steps"]["6"]["owner"], "executor")
            self.assertEqual(manifest["status"], "step5-prepared")
            self.assertTrue(manifest["readiness"]["step6_entry_ready"])
            self.assertEqual(manifest["target_validation_objects"], contract["validation_objects"])

            governance_dir = root / ".governance"
            agent_entry = (governance_dir / "AGENTS.md").read_text(encoding="utf-8")
            agent_playbook = (governance_dir / "agent-playbook.md").read_text(encoding="utf-8")
            current_state = (governance_dir / "current-state.md").read_text(encoding="utf-8")
            self.assertIn("Agent-first open-cowork project", agent_entry)
            self.assertIn("Do not ask the human to memorize ocw commands", agent_entry)
            self.assertIn("Current phase: Phase 2", current_state)
            self.assertIn("Current step: Step 5", current_state)
            self.assertIn("Executor: executor-agent", current_state)
            self.assertIn("Project goal: Use open-cowork", current_state)
            self.assertIn("Human update template", agent_playbook)
            self.assertIn("Need human decision", agent_playbook)

            validate_stdout = io.StringIO()
            with contextlib.redirect_stdout(validate_stdout):
                validate_exit = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-PREPARE"])
            self.assertEqual(validate_exit, 0)
            self.assertIn("Contract valid", validate_stdout.getvalue())

    def test_change_prepare_records_source_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-SOURCE-DOCS", "--title", "Source docs"])

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-SOURCE-DOCS",
                    "--goal",
                    "Bind source documents to a change package",
                    "--source-doc",
                    "docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md",
                    "--source-doc",
                    "docs/archive/reports/2026-04-24-v025-agent-first-dogfood-findings.md",
                ])

            change_dir = root / ".governance/changes/CHG-SOURCE-DOCS"
            manifest = load_yaml(change_dir / "manifest.yaml")
            self.assertEqual(exit_code, 0)
            self.assertEqual(manifest["source_docs"], [
                "docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md",
                "docs/archive/reports/2026-04-24-v025-agent-first-dogfood-findings.md",
            ])
            self.assertIn("58-v0.2.6", (change_dir / "requirements.md").read_text(encoding="utf-8"))
            self.assertIn("v025-agent-first-dogfood", (change_dir / "intent.md").read_text(encoding="utf-8"))

    def test_participants_setup_writes_personal_profile_and_updates_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-PARTICIPANTS", "--title", "Participants"])
                main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-PARTICIPANTS",
                    "--goal",
                    "Configure human-visible personal-domain participants",
                ])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "participants",
                    "setup",
                    "--profile",
                    "personal",
                    "--participant",
                    "codex-agent:executor,implementation",
                    "--participant",
                    "human-sponsor:final-decision",
                    "--change-id",
                    "CHG-PARTICIPANTS",
                ])

            self.assertEqual(exit_code, 0)
            self.assertIn("9-step owner matrix", stdout.getvalue())
            profile = load_yaml(root / ".governance/participants.yaml")
            bindings = load_yaml(root / ".governance/changes/CHG-PARTICIPANTS/bindings.yaml")
            self.assertEqual(profile["schema"], "participants-profile/v1")
            self.assertEqual(len(profile["step_owner_matrix"]), 9)
            self.assertEqual(profile["step_owner_matrix"][0]["primary_owner"], "human-sponsor")
            self.assertEqual(bindings["participants_profile_ref"], ".governance/participants.yaml")
            self.assertEqual(bindings["steps"][1]["owner"], "human-sponsor")
            self.assertTrue(bindings["steps"][5]["human_gate"])
            self.assertEqual(bindings["steps"][8]["reviewer"], "independent-reviewer")

    def test_intent_capture_and_confirm_records_human_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-INTENT", "--title", "Intent"])
                main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-INTENT",
                    "--goal",
                    "Clarify real project intent before execution",
                    "--scope-in",
                    "src/**",
                    "--scope-out",
                    "docs/archive/**",
                ])

            with contextlib.redirect_stdout(io.StringIO()):
                capture_exit = main([
                    "--root",
                    str(root),
                    "intent",
                    "capture",
                    "--change-id",
                    "CHG-INTENT",
                    "--project-intent",
                    "Ship a human-visible control baseline",
                    "--requirement",
                    "Participants matrix is visible",
                    "--optimization",
                    "Reduce CLI-first burden",
                    "--bug",
                    "current-state can become stale after archive",
                    "--acceptance",
                    "Human can confirm scope before execution",
                    "--risk",
                    "Over-scoping v0.2.7",
                    "--open-question",
                    "Should gates be hard or advisory first?",
                ])
            self.assertEqual(capture_exit, 0)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                confirm_exit = main([
                    "--root",
                    str(root),
                    "intent",
                    "confirm",
                    "--change-id",
                    "CHG-INTENT",
                    "--confirmed-by",
                    "human-sponsor",
                    "--note",
                    "Scope accepted for v0.2.7 baseline",
                ])

            self.assertEqual(confirm_exit, 0)
            self.assertIn("Intent confirmed", stdout.getvalue())
            payload = load_yaml(root / ".governance/changes/CHG-INTENT/intent-confirmation.yaml")
            manifest = load_yaml(root / ".governance/changes/CHG-INTENT/manifest.yaml")
            self.assertEqual(payload["status"], "confirmed")
            self.assertEqual(payload["human_confirmation"]["confirmed_by"], "human-sponsor")
            self.assertIn("Participants matrix is visible", payload["requirements"])
            self.assertEqual(manifest["intent_confirmation"]["status"], "confirmed")
            self.assertTrue((root / ".governance/changes/CHG-INTENT/INTENT_CONFIRMATION.md").exists())

    def test_step_report_materializes_human_visible_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-STEP", "--title", "Step report"])
                main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-STEP",
                    "--goal",
                    "Show a human-visible step report",
                ])
                main(["--root", str(root), "participants", "setup", "--change-id", "CHG-STEP"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "step",
                    "report",
                    "--change-id",
                    "CHG-STEP",
                    "--step",
                    "5",
                ])

            self.assertEqual(exit_code, 0)
            self.assertIn("Step report written", stdout.getvalue())
            report = load_yaml(root / ".governance/changes/CHG-STEP/step-reports/step-5.yaml")
            report_text = (root / ".governance/changes/CHG-STEP/step-reports/step-5.md").read_text(encoding="utf-8")
            self.assertEqual(report["schema"], "step-report/v1")
            self.assertEqual(report["owner"], "human-sponsor")
            self.assertTrue(report["human_gate"])
            self.assertIn("Confirm project intent", " ".join(report["human_decisions_required"]))
            self.assertIn("Human decisions required", report_text)

    def test_adopt_dry_run_outputs_agent_first_plan_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "change", "create", "ACTIVE-CHANGE", "--title", "Active work"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "adopt",
                    "--target",
                    str(root),
                    "--goal",
                    "Install open-cowork and govern the current project iteration",
                    "--source-doc",
                    "docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md",
                    "--source-doc",
                    "docs/archive/plans/59-v0.2.7-first-step-personal-agent-dogfood-requirements.md",
                    "--agent",
                    "Openclaw",
                    "--agent",
                    "Codex",
                    "--agent",
                    "OOSO",
                    "--dry-run",
                    "--format",
                    "json",
                ])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["schema"], "adoption-plan/v1")
            self.assertEqual(payload["target"], str(root.resolve()))
            self.assertEqual(payload["goal"], "Install open-cowork and govern the current project iteration")
            self.assertEqual(payload["source_docs"], [
                "docs/archive/plans/58-v0.2.6-agent-first-dogfood-requirements.md",
                "docs/archive/plans/59-v0.2.7-first-step-personal-agent-dogfood-requirements.md",
            ])
            self.assertEqual(payload["active_change"]["change_id"], "ACTIVE-CHANGE")
            self.assertTrue(payload["active_change"]["requires_lifecycle_decision"])
            self.assertIn("continue", payload["active_change"]["allowed_policies"])
            self.assertIn(".governance/current-state.md", payload["recommended_read_set"])
            self.assertEqual(payload["role_suggestions"]["Openclaw"], ["orchestrator"])
            self.assertEqual(payload["role_suggestions"]["Codex"], ["executor", "verifier"])
            self.assertEqual(payload["role_suggestions"]["OOSO"], ["reviewer", "verification_assistant"])
            self.assertFalse((root / ".governance/changes/install-open-cowork-and-govern-the-current-project-iteration").exists())

    def test_change_prepare_requires_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-NO-GOAL", "--title", "Missing goal"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "change", "prepare", "CHG-NO-GOAL"])

            self.assertEqual(exit_code, 1)
            self.assertIn("--goal is required", stdout.getvalue())

    def test_pilot_prepares_personal_change_from_one_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target-project"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "pilot",
                    "--target",
                    str(target),
                    "--change-id",
                    "personal-demo",
                    "--title",
                    "Personal pilot",
                    "--goal",
                    "Prepare a governed personal-domain trial",
                    "--scope-in",
                    "src/**",
                    "--verify-command",
                    "python3 -m unittest discover -s tests",
                    "--yes",
                ])

            output = stdout.getvalue()
            change_dir = target / ".governance/changes/personal-demo"
            self.assertEqual(exit_code, 0)
            self.assertTrue((change_dir / "contract.yaml").exists())
            self.assertTrue((change_dir / "bindings.yaml").exists())
            self.assertTrue((target / ".governance/AGENTS.md").exists())
            self.assertTrue((target / ".governance/current-state.md").exists())
            self.assertIn("open-cowork pilot complete", output)
            self.assertIn("Contract valid", output)
            self.assertIn("# open-cowork status", output)
            self.assertIn("## Blockers\n- none", output)
            self.assertNotIn("Manifest target_validation_objects must align", output)
            self.assertIn("Agent-first handoff ready", output)
            self.assertIn(".governance/AGENTS.md", output)
            self.assertNotIn("copy this prompt to your personal-domain Agent", output)
            self.assertEqual(load_yaml(change_dir / "manifest.yaml")["status"], "step5-prepared")

    def test_pilot_default_change_id_is_current_iteration(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target-project"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "pilot",
                    "--target",
                    str(target),
                    "--goal",
                    "Prepare the current project iteration",
                    "--yes",
                ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((target / ".governance/changes/current-iteration/contract.yaml").exists())
            self.assertIn("current-iteration", stdout.getvalue())

    def test_pilot_blocks_existing_active_change_without_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target-project"
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(target), "init"])
                main(["--root", str(target), "change", "create", "ACTIVE", "--title", "Active"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "pilot",
                    "--target",
                    str(target),
                    "--change-id",
                    "NEXT",
                    "--title",
                    "Next",
                    "--goal",
                    "Prepare next pilot",
                    "--yes",
                ])

            self.assertEqual(exit_code, 1)
            self.assertIn("Active change lifecycle decision required", stdout.getvalue())

    def test_repository_agent_first_docs_exist(self):
        repo_root = Path(__file__).resolve().parents[1]
        agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
        adoption = (repo_root / "docs/agent-adoption.md").read_text(encoding="utf-8")
        playbook = (repo_root / "docs/agent-playbook.md").read_text(encoding="utf-8")

        self.assertIn("Agent-first", agents)
        self.assertIn("安装 open-cowork，并在当前项目中实施这套协同治理框架", agents)
        self.assertIn("do not make the human operate open-cowork as a CLI-first tool", agents)
        self.assertIn("人表达意图", adoption)
        self.assertIn("Agent 调用 open-cowork", adoption)
        self.assertIn("当前项目推进状态", playbook)

    def test_contract_validate_and_run_review_archive_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-2",
                    "--title",
                    "CLI lifecycle",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-2"
            contract_path = change_dir / "contract.yaml"
            write_yaml(contract_path, {
                "objective": "milestone1-stage1-cli-closure",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["StateConsistencyCheck"],
                "verification": {"commands": ["python3 -m unittest discover -s tests -v"], "checks": ["evidence persisted"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            manifest["target_validation_objects"] = ["StateConsistencyCheck"]
            write_yaml(change_dir / "manifest.yaml", manifest)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                validate_exit = main(["--root", str(root), "contract", "validate", "--change-id", "CHG-CLI-2"])
            self.assertEqual(validate_exit, 0)
            self.assertIn("Contract valid", stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                run_exit = main([
                    "--root",
                    str(root),
                    "run",
                    "--change-id",
                    "CHG-CLI-2",
                    "--command",
                    "python3 -m unittest discover -s tests -v",
                    "--command-output",
                    "ok",
                    "--test-output",
                    "tests passed",
                    "--evidence-ref",
                    "evidence/first-instruction-dogfood-result.md",
                    "--created",
                    "src/governance/runtime_stage1.py",
                    "--modified",
                    "tests/test_cli.py",
                ])
            self.assertEqual(run_exit, 0)
            self.assertTrue((change_dir / "evidence/execution-summary.yaml").exists())
            execution_summary = load_yaml(change_dir / "evidence/execution-summary.yaml")
            self.assertIn("evidence/first-instruction-dogfood-result.md", execution_summary["evidence_refs"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                verify_exit = main([
                    "--root",
                    str(root),
                    "verify",
                    "--change-id",
                    "CHG-CLI-2",
                ])
            self.assertEqual(verify_exit, 0)
            verify_payload = load_yaml(change_dir / "verify.yaml")
            self.assertEqual(verify_payload["summary"]["status"], "pass")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                review_exit = main([
                    "--root",
                    str(root),
                    "review",
                    "--change-id",
                    "CHG-CLI-2",
                    "--decision",
                    "approve",
                    "--reviewer",
                    "reviewer-agent",
                    "--rationale",
                    "Stage 1 minimum chain accepted",
                ])
            self.assertEqual(review_exit, 0)
            review_payload = load_yaml(change_dir / "review.yaml")
            self.assertEqual(review_payload["decision"]["status"], "approve")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                archive_exit = main(["--root", str(root), "archive", "--change-id", "CHG-CLI-2"])
            self.assertEqual(archive_exit, 0)

            archive_dir = root / ".governance/archive/CHG-CLI-2"
            self.assertTrue((archive_dir / "manifest.yaml").exists())
            self.assertTrue((archive_dir / "archive-receipt.yaml").exists())
            archive_receipt = load_yaml(archive_dir / "archive-receipt.yaml")
            self.assertTrue(archive_receipt["archive_executed"])

            current_change = read_current_change(root)
            changes_index = read_changes_index(root)
            maintenance = load_yaml(root / ".governance/index/maintenance-status.yaml")
            self.assertEqual(current_change["status"], "idle")
            self.assertIsNone(current_change["current_change_id"])
            self.assertEqual(changes_index["changes"][0]["status"], "archived")
            self.assertEqual(maintenance["last_archived_change"], "CHG-CLI-2")
            current_state = (root / ".governance/current-state.md").read_text(encoding="utf-8")
            self.assertIn("Lifecycle: idle", current_state)
            self.assertIn("Last archived change: CHG-CLI-2", current_state)

            month_file = root / ".governance/runtime/timeline" / f"events-{__import__('datetime').datetime.utcnow().strftime('%Y%m')}.yaml"
            payload = load_yaml(month_file)
            self.assertTrue(any(
                event["change_id"] == "CHG-CLI-2" and event["event_type"] == "run_completed"
                for event in payload["events"]
            ))

    def test_review_requires_verify_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-REVIEW",
                    "--title",
                    "Review gate",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-REVIEW"
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                review_exit = main([
                    "--root",
                    str(root),
                    "review",
                    "--change-id",
                    "CHG-CLI-REVIEW",
                    "--decision",
                    "approve",
                    "--reviewer",
                    "reviewer-agent",
                    "--rationale",
                    "Should fail before verify",
                ])

            self.assertEqual(review_exit, 1)
            self.assertIn("Review failed", stdout.getvalue())
            self.assertEqual(load_yaml(change_dir / "review.yaml"), {})
            month_file = root / ".governance/runtime/timeline" / f"events-{__import__('datetime').datetime.utcnow().strftime('%Y%m')}.yaml"
            payload = load_yaml(month_file)
            self.assertTrue(any(
                event["change_id"] == "CHG-CLI-REVIEW"
                and event["event_type"] == "gate_blocked"
                and event["step"] == 8
                for event in payload["events"]
            ))

    def test_verify_requires_step6_execution_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-VERIFY",
                    "--title",
                    "Verify gate",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-VERIFY"
            (change_dir / "evidence").mkdir(exist_ok=True)
            write_yaml(change_dir / "evidence/execution-summary.yaml", {
                "status": "success",
                "artifacts": {"created": [], "modified": []},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                verify_exit = main([
                    "--root",
                    str(root),
                    "verify",
                    "--change-id",
                    "CHG-CLI-VERIFY",
                ])

            self.assertEqual(verify_exit, 1)
            self.assertIn("Verify failed", stdout.getvalue())

    def test_verify_can_retry_from_step7_blocked_after_consistency_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "change", "create", "CHG-VERIFY-RETRY", "--title", "Verify retry"])

            change_dir = root / ".governance/changes/CHG-VERIFY-RETRY"
            validation_objects = [
                ".governance/changes/CHG-VERIFY-RETRY/contract.yaml",
                ".governance/changes/CHG-VERIFY-RETRY/bindings.yaml",
                "src/**",
            ]
            write_yaml(change_dir / "contract.yaml", {
                "objective": "retry verify after a blocker is fixed",
                "scope_in": ["src/**", ".governance/changes/CHG-VERIFY-RETRY/evidence/**"],
                "scope_out": [".governance/index/**", ".governance/runtime/**", ".governance/archive/**"],
                "allowed_actions": ["edit_files", "write_evidence"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": validation_objects,
                "verification": {"commands": ["python3 -m unittest"], "checks": ["state consistency"]},
                "evidence_expectations": {"required": ["command_output", "test_output", "changed_files_manifest"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "contract-required"},
                    "7": {"owner": "verifier-agent", "gate": "evidence-required"},
                    "8": {"owner": "reviewer-agent", "gate": "independent-review-required"},
                },
            })
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["status"] = "step7-blocked"
            manifest["current_step"] = 7
            manifest["target_validation_objects"] = validation_objects
            write_yaml(change_dir / "manifest.yaml", manifest)
            (change_dir / "evidence").mkdir(exist_ok=True)
            write_yaml(change_dir / "evidence/execution-summary.yaml", {
                "status": "success",
                "command_output": "ok",
                "test_output": "ok",
                "artifacts": {"created": ["src/example.py"], "modified": []},
            })
            entry = {
                "change_id": "CHG-VERIFY-RETRY",
                "path": ".governance/changes/CHG-VERIFY-RETRY",
                "status": "step7-blocked",
                "current_step": 7,
            }
            set_current_change(root, entry)
            upsert_change_entry(root, entry)
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "step7-blocked",
                "current_change_active": "step7-blocked",
                "current_change_id": "CHG-VERIFY-RETRY",
                "last_archived_change": None,
                "last_archive_at": None,
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                verify_exit = main(["--root", str(root), "verify", "--change-id", "CHG-VERIFY-RETRY"])

            self.assertEqual(verify_exit, 0)
            self.assertIn("Verify recorded", stdout.getvalue())
            self.assertEqual(load_yaml(change_dir / "verify.yaml")["summary"]["status"], "pass")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                verify_exit = main(["--root", str(root), "verify", "--change-id", "CHG-VERIFY-RETRY"])

            self.assertEqual(verify_exit, 0)
            self.assertIn("Verify recorded", stdout.getvalue())
            self.assertEqual(load_yaml(change_dir / "verify.yaml")["summary"]["status"], "pass")

    def test_review_requires_step7_verified_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-REVIEW-STATE",
                    "--title",
                    "Review state gate",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-REVIEW-STATE"
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["status"] = "step6-executed-pre-step7"
            manifest["current_step"] = 6
            write_yaml(change_dir / "manifest.yaml", manifest)
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-CLI-REVIEW-STATE",
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                review_exit = main([
                    "--root",
                    str(root),
                    "review",
                    "--change-id",
                    "CHG-CLI-REVIEW-STATE",
                    "--decision",
                    "approve",
                    "--reviewer",
                    "reviewer-agent",
                    "--rationale",
                    "Should fail before step7 state is recorded",
                ])

            self.assertEqual(review_exit, 1)
            self.assertIn("Review failed", stdout.getvalue())

    def test_run_rejects_execution_after_step7_without_mutating_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "CHG-RUN-LATE", "--title", "Late run"])
                main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "CHG-RUN-LATE",
                    "--goal",
                    "Prevent late run mutation",
                ])

            change_dir = root / ".governance/changes/CHG-RUN-LATE"
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["status"] = "step7-blocked"
            manifest["current_step"] = 7
            write_yaml(change_dir / "manifest.yaml", manifest)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                run_exit = main([
                    "--root",
                    str(root),
                    "run",
                    "--change-id",
                    "CHG-RUN-LATE",
                    "--command-output",
                    "late",
                    "--test-output",
                    "late",
                    "--created",
                    "src/late.py",
                ])

            self.assertEqual(run_exit, 1)
            self.assertIn("cannot run from step 7", stdout.getvalue())
            self.assertEqual(load_yaml(change_dir / "manifest.yaml")["status"], "step7-blocked")

    def test_archive_requires_approved_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-ARCHIVE",
                    "--title",
                    "Archive gate",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-ARCHIVE"
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": "CHG-CLI-ARCHIVE",
                "decision": {"status": "revise", "rationale": "not ready"},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                archive_exit = main([
                    "--root",
                    str(root),
                    "archive",
                    "--change-id",
                    "CHG-CLI-ARCHIVE",
                ])

            self.assertEqual(archive_exit, 1)
            self.assertIn("Archive failed", stdout.getvalue())
            self.assertFalse((root / ".governance/archive/CHG-CLI-ARCHIVE").exists())

    def test_archive_requires_step8_review_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-ARCHIVE-STATE",
                    "--title",
                    "Archive state gate",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-ARCHIVE-STATE"
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": "CHG-CLI-ARCHIVE-STATE",
                "decision": {"status": "approve", "rationale": "looks good"},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                archive_exit = main([
                    "--root",
                    str(root),
                    "archive",
                    "--change-id",
                    "CHG-CLI-ARCHIVE-STATE",
                ])

            self.assertEqual(archive_exit, 1)
            self.assertIn("Archive failed", stdout.getvalue())
            self.assertFalse((root / ".governance/archive/CHG-CLI-ARCHIVE-STATE").exists())

    def test_status_outputs_human_facing_phase_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-CLI-3",
                    "--title",
                    "Human snapshot",
                ])

            change_dir = root / ".governance/changes/CHG-CLI-3"
            write_yaml(change_dir / "contract.yaml", {
                "objective": "surface-project-status-clearly",
                "scope_in": [".governance/**", "src/**", "tests/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HumanStatusSnapshot"],
                "verification": {"commands": ["python3 -m unittest discover -s tests -v"], "checks": ["status snapshot visible"]},
                "evidence_expectations": {"required": ["changed_files_manifest", "command_output", "test_output", "file_diff"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDeliver a human-readable progress snapshot.\n", encoding="utf-8")
            manifest = load_yaml(change_dir / "manifest.yaml")
            manifest["status"] = "step6-executed-pre-step7"
            manifest["current_step"] = 6
            manifest.setdefault("readiness", {})["step6_entry_ready"] = True
            manifest["roles"] = {"executor": "executor-agent", "reviewer": "reviewer-agent", "formal_orchestrator": "pm-agent"}
            manifest["target_validation_objects"] = ["HumanStatusSnapshot"]
            write_yaml(change_dir / "manifest.yaml", manifest)
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step6-executed-pre-step7",
                "current_change_id": "CHG-CLI-3",
                "current_step": 6,
                "current_change": {
                    "change_id": "CHG-CLI-3",
                    "status": "step6-executed-pre-step7",
                    "current_step": 6,
                },
            })
            upsert_change_entry(root, {
                "change_id": "CHG-CLI-3",
                "path": ".governance/changes/CHG-CLI-3",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "title": "Human snapshot",
                "validation_focus": "human-status-surface",
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "status"])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("current_phase: Phase 3 / 执行与验证", output)
            self.assertIn("current_owner: executor-agent", output)
            self.assertIn("waiting_on: Step 7 verify outputs and review-ready decision", output)
            self.assertIn("next_decision: Step 8 / Review and decide", output)
            self.assertIn("project_summary: Deliver a human-readable progress snapshot.", output)
            self.assertTrue((change_dir / "STATUS_SNAPSHOT.yaml").exists())

    def test_status_after_change_create_reports_draft_contract_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-DRAFT-STATUS",
                    "--title",
                    "Draft status should be readable",
                ])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "status"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("current_status: drafting", output)
            self.assertIn("waiting_on: contract.yaml", output)
            self.assertIn("next_action: complete contract.yaml and bindings.yaml", output)
            self.assertIn("project_summary: Draft status should be readable", output)
            self.assertNotIn("Status check failed", output)
            self.assertNotIn("missing required field", output)

    def test_continuity_digest_after_change_create_reports_draft_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    "CHG-DRAFT-DIGEST",
                    "--title",
                    "Draft digest should be readable",
                ])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "continuity", "digest", "--change-id", "CHG-DRAFT-DIGEST"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Continuity digest unavailable for draft change", output)
            self.assertIn("CHG-DRAFT-DIGEST", output)
            self.assertIn("ocw --root . status", output)
            self.assertNotIn("Traceback", output)
            self.assertNotIn("missing required field", output)

    def test_onboard_quickstart_initializes_target_and_runs_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target-project"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["onboard", "--target", str(target), "--mode", "quickstart", "--yes"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertTrue((target / ".governance/index/current-change.yaml").exists())
            self.assertIn("open-cowork onboard", output)
            self.assertIn("mode: quickstart", output)
            self.assertIn("Initialized open-cowork governance", output)
            self.assertIn("# open-cowork status", output)
            self.assertIn("# Session Execution Diagnosis", output)
            self.assertIn("onboard complete", output)
            self.assertNotIn("personal-demo", output)
            self.assertIn("ocw adopt", output)

    def test_onboard_manual_mode_prints_plan_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "manual-project"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["onboard", "--target", str(target), "--mode", "manual"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertFalse((target / ".governance").exists())
            self.assertIn("Manual onboarding plan", output)
            self.assertIn("ocw --root", output)

    def test_setup_alias_runs_onboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "setup-project"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["setup", "--target", str(target), "--yes", "--no-diagnose"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertTrue((target / ".governance/index/current-change.yaml").exists())
            self.assertIn("mode: quickstart", output)
            self.assertNotIn("# Session Execution Diagnosis", output)

    def test_onboard_yes_without_target_defaults_to_current_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous_cwd = Path.cwd()
            try:
                os.chdir(tmp)

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(["onboard", "--yes", "--no-diagnose"])

                output = stdout.getvalue()
                self.assertEqual(exit_code, 0)
                self.assertTrue((Path(tmp) / ".governance/index/current-change.yaml").exists())
                self.assertIn(f"- target: {Path(tmp).resolve()}", output)
            finally:
                os.chdir(previous_cwd)

    def test_hygiene_command_classifies_repo_governance_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            (root / ".governance/AGENTS.md").write_text("# Agent entry\n", encoding="utf-8")
            (root / ".governance/current-state.md").write_text("# Current State\n", encoding="utf-8")
            (root / ".governance/agent-playbook.md").write_text("# Playbook\n", encoding="utf-8")
            (root / "docs/archive/plans").mkdir(parents=True, exist_ok=True)
            (root / "docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md").write_text("# Change Package\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "hygiene", "--format", "json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["schema"], "hygiene-report/v1")
            self.assertIn(".governance/index/current-change.yaml", payload["runtime_generated"])
            self.assertIn(".governance/AGENTS.md", payload["agent_handoff_files"])
            self.assertNotIn("docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md", payload["pending_docs"])
            self.assertIn("docs/archive/plans/60-v0.2.6-agent-first-adoption-closure-change-package.md", payload["cold_archive_docs"])
            self.assertIn(".governance/changes/**", payload["ignored_artifact_patterns"])
            self.assertIn(".governance/AGENTS.md", payload["suggested_commit"])
            self.assertIn(".governance/changes/**", payload["suggested_ignore"])
            self.assertTrue(payload["suggested_cleanup"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                alias_exit = main(["--root", str(root), "doctor"])
            self.assertEqual(alias_exit, 0)
            self.assertIn("open-cowork hygiene", stdout.getvalue())

    def test_hygiene_reports_current_state_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
            (root / ".governance/current-state.md").write_text(
                "# open-cowork Current State\n\nLifecycle: idle\nLast archived change: None\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "hygiene", "--format", "json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["state_consistency"]["status"], "pass")

            (root / ".governance/current-state.md").write_text(
                "# open-cowork Current State\n\nActive change: stale-change\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", str(root), "doctor", "--format", "json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["state_consistency"]["status"], "blocker")

    def test_change_prepare_blocks_silent_active_change_switch_without_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "init"])
                main(["--root", str(root), "change", "create", "ACTIVE", "--title", "Active"])
                main(["--root", str(root), "change", "create", "NEXT", "--title", "Next"])
            set_current_change(root, {
                "change_id": "ACTIVE",
                "path": ".governance/changes/ACTIVE",
                "status": "drafting",
                "current_step": 5,
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "NEXT",
                    "--goal",
                    "Prepare next without lifecycle policy",
                ])

            self.assertEqual(exit_code, 1)
            self.assertIn("Active change lifecycle decision required", stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                force_exit = main([
                    "--root",
                    str(root),
                    "change",
                    "prepare",
                    "NEXT",
                    "--goal",
                    "Prepare next with explicit force policy",
                    "--active-policy",
                    "force",
                ])
            self.assertEqual(force_exit, 0)
            self.assertIn("Change prepared: NEXT", stdout.getvalue())

    def test_pyproject_exposes_open_cowork_console_alias(self):
        pyproject_text = Path(__file__).resolve().parents[1].joinpath("pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('ocw = "governance.cli:main"', pyproject_text)
        self.assertIn('open-cowork = "governance.cli:main"', pyproject_text)

    def test_version_command_reports_version_and_paths(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["version"])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("open-cowork 0.2.9", output)
        self.assertIn("python:", output)
        self.assertIn("cli:", output)
        self.assertIn("project_root:", output)

    def test_continuity_commands_materialize_launch_input_and_round_entry_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            current_change = "CHG-CLI-4"
            predecessor_change = "CHG-CLI-3"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main([
                    "--root",
                    str(root),
                    "change",
                    "create",
                    current_change,
                    "--title",
                    "Continuity packet",
                ])

            set_current = {
                "change_id": current_change,
                "path": f".governance/changes/{current_change}",
                "status": "step5-prepared",
                "current_step": 5,
            }
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step5-prepared",
                "current_change_id": current_change,
                "current_step": 5,
                "current_change": set_current,
            })
            changes_index = read_changes_index(root)
            changes_index["changes"][0]["predecessor_change"] = predecessor_change
            write_yaml(root / ".governance/index/changes-index.yaml", changes_index)
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "preparing-next-round",
                "current_change_active": True,
                "current_change_id": current_change,
                "last_archived_change": predecessor_change,
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": predecessor_change,
                    "archive_path": f".governance/archive/{predecessor_change}/",
                    "archived_at": "2026-04-20T00:00:00Z",
                    "receipt": f".governance/archive/{predecessor_change}/archive-receipt.yaml",
                }],
            })
            archive_dir = root / f".governance/archive/{predecessor_change}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "review.yaml", {
                "decision": {"status": "approve"},
                "pre_step9_condition_closure": {"step9_entry_ready": True},
                "statement": {"not_step9_archive": True},
            })
            write_yaml(archive_dir / "manifest.yaml", {"lifecycle": {"step9": {"status": "completed"}}})
            write_yaml(archive_dir / "archive-receipt.yaml", {"archive_executed": True, "archived_at": "2026-04-20T00:00:00Z"})

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                launch_exit = main(["--root", str(root), "continuity", "launch-input", "--change-id", current_change])
            self.assertEqual(launch_exit, 0)
            self.assertIn("continuity-launch-input.yaml", stdout.getvalue())
            launch_payload = load_yaml(root / f".governance/changes/{current_change}/continuity-launch-input.yaml")
            self.assertEqual(launch_payload["decision_summary"]["current_phase"], "Phase 2 / 方案与准备")
            self.assertEqual(launch_payload["decision_summary"]["next_decision"], "Step 5 / Approve the start")
            self.assertTrue(launch_payload["decision_summary"]["next_input_suggestion"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                summary_exit = main(["--root", str(root), "continuity", "round-entry-summary", "--change-id", current_change])
            self.assertEqual(summary_exit, 0)
            self.assertIn("ROUND_ENTRY_INPUT_SUMMARY.yaml", stdout.getvalue())

            self.assertTrue((root / f".governance/changes/{current_change}/continuity-launch-input.yaml").exists())
            self.assertTrue((root / f".governance/changes/{current_change}/ROUND_ENTRY_INPUT_SUMMARY.yaml").exists())

    def test_continuity_handoff_package_command_materializes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-HO"

            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "CLI handoff package",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "emit handoff package from CLI",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["HandoffPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nEmit handoff package from CLI.\n", encoding="utf-8")
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step6-executed-pre-step7",
                "current_change_id": change_id,
                "current_step": 6,
                "current_change": {
                    "change_id": change_id,
                    "status": "step6-executed-pre-step7",
                    "current_step": 6,
                },
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step6-executed-pre-step7",
                "current_step": 6,
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "step6-executed-pre-step7",
                "current_change_active": "step6-executed-pre-step7",
                "current_change_id": change_id,
                "last_archived_change": None,
                "last_archive_at": None,
                "residual_followups": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "handoff-package",
                    "--change-id", change_id,
                ])

            self.assertEqual(exit_code, 0)
            self.assertIn("Handoff package written:", stdout.getvalue())
            handoff_path = root / f".governance/changes/{change_id}/handoff-package.yaml"
            self.assertTrue(handoff_path.exists())
            handoff = load_yaml(handoff_path)
            self.assertIn("recommended_read_set", handoff)
            self.assertIn(".governance/current-state.md", handoff["recommended_read_set"])
            self.assertIn(f".governance/changes/{change_id}/contract.yaml", handoff["recommended_read_set"])
            self.assertIn("Do not full-scan archive history", handoff["context_budget_rule"])



    def test_continuity_closeout_packet_command_materializes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-CLOSE"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00+00:00",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00+00:00",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "CLI closeout",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "contract.yaml", {"objective": "closeout packet"})
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "closeout-packet",
                    "--change-id", change_id,
                    "--closeout-statement", "本轮已完成最小闭环并正式归档",
                    "--delivered-scope", "continuity primitives",
                    "--deferred-scope", "sync / escalation packet",
                    "--key-outcome", "continuity primitives 形成最小链",
                    "--unresolved-item", "sync packet 尚未建立",
                    "--next-direction", "build sync / escalation packet",
                    "--attention-point", "不要把 closeout-packet 扩成新的 truth-source",
                    "--carry-forward-item", "project-to-higher-layer sync",
                    "--operator-summary", "本轮已完成 continuity primitives 基线",
                    "--sponsor-summary", "本轮完成 continuity 主线基线",
                ])
            self.assertEqual(exit_code, 0)
            payload = load_yaml(archive_dir / "closeout-packet.yaml")
            self.assertEqual(payload["schema"], "closeout-packet/v1")
            self.assertIn("Closeout packet written", stdout.getvalue())



    def test_continuity_sync_packet_command_materializes_output_from_closeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-SYNC"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "closeout-packet.yaml", {
                "schema": "closeout-packet/v1",
                "change_id": change_id,
                "closure_summary": {
                    "final_status": "archived",
                    "closeout_statement": "本轮已完成最小闭环并正式归档",
                },
                "refs": {
                    "runtime_timeline": ".governance/runtime/timeline/events-202604.yaml",
                },
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-packet",
                    "--change-id", change_id,
                    "--source-kind", "closeout",
                    "--sync-kind", "escalation",
                    "--target-layer", "sponsor",
                    "--target-scope", "project-level",
                    "--urgency", "attention",
                    "--headline", "建议进入更高层同步阶段",
                    "--delivered-scope", "closeout-packet",
                    "--pending-scope", "ecosystem-level sync",
                    "--requested-attention", "确认上层同步边界",
                    "--requested-decision", "是否以 sync-packet 作为默认上层输入",
                    "--next-owner-suggestion", "sponsor-or-ecosystem-operator",
                    "--next-action-suggestion", "review sync packet and decide next-level integration",
                ])
            self.assertEqual(exit_code, 0)
            payload = load_yaml(archive_dir / "sync-packet.yaml")
            self.assertEqual(payload["schema"], "sync-packet/v1")
            self.assertIn("Sync packet written", stdout.getvalue())



    def test_continuity_sync_history_command_appends_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-HIST"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "sync-packet.yaml", {
                "schema": "sync-packet/v1",
                "change_id": change_id,
                "generated_at": "2026-04-24T12:00:00Z",
                "sync_kind": "escalation",
                "source_anchor": {"source_kind": "closeout"},
                "target_context": {"target_layer": "sponsor", "target_scope": "project-level"},
                "sync_summary": {"headline": "需要更高层同步"},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history",
                    "--change-id", change_id,
                    "--source-kind", "closeout",
                ])
            self.assertEqual(exit_code, 0)
            self.assertIn("Sync history written", stdout.getvalue())

    def test_continuity_sync_history_query_command_supports_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-CLI-HIST-Q",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "closeout",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/archive/CHG-CLI-HIST-Q/sync-packet.yaml",
                    "headline": "需要更高层同步",
                }],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--change-id", "CHG-CLI-HIST-Q",
                    "--format", "json",
                ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema"], "sync-history-query/v1")
            self.assertEqual(payload["summary"]["matched_events"], 1)

    def test_continuity_sync_history_query_command_supports_text_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-CLI-HIST-TEXT",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "routine-sync",
                    "source_kind": "increment",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/changes/CHG-CLI-HIST-TEXT/sync-packet.yaml",
                    "headline": "阶段同步",
                }],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Sync history month: 202604", output)
            self.assertIn("matched events: 1", output)
            self.assertIn("CHG-CLI-HIST-TEXT", output)

    def test_continuity_sync_history_months_command_supports_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202605.yaml", {"schema": "sync-history/v1", "month": "202605", "events": []})
            write_yaml(history_dir / "events-202604.yaml", {"schema": "sync-history/v1", "month": "202604", "events": []})

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-months",
                    "--format", "json",
                ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema"], "sync-history-months/v1")
            self.assertEqual(payload["months"], ["202604", "202605"])

    def test_continuity_sync_history_query_command_supports_all_months_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-CLI-HIST-ALL",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "closeout",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/archive/CHG-CLI-HIST-ALL/sync-packet.yaml",
                    "headline": "A",
                }],
            })
            write_yaml(history_dir / "events-202605.yaml", {
                "schema": "sync-history/v1",
                "month": "202605",
                "events": [{
                    "event_id": "evt-2",
                    "change_id": "CHG-CLI-HIST-ALL",
                    "recorded_at": "2026-05-01T12:00:00Z",
                    "sync_kind": "routine-sync",
                    "source_kind": "increment",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/changes/CHG-CLI-HIST-ALL/sync-packet.yaml",
                    "headline": "B",
                }],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--all-months",
                    "--change-id", "CHG-CLI-HIST-ALL",
                    "--format", "json",
                ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema"], "sync-history-query/v1")
            self.assertEqual(payload["month"], "all")
            self.assertEqual(payload["summary"]["total_events"], 2)
            self.assertEqual(payload["summary"]["matched_events"], 2)

    def test_continuity_sync_history_query_command_supports_grouped_summary_text_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-CLI-SUMMARY",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-CLI-SUMMARY/sync-packet.yaml",
                        "headline": "首次同步",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-CLI-SUMMARY",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-CLI-SUMMARY/sync-packet.yaml",
                        "headline": "二次同步",
                    },
                ],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--summary-by", "change_id",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("grouped summary by: change_id", output)
            self.assertIn("CHG-CLI-SUMMARY", output)
            self.assertIn("events=2", output)

    def test_continuity_sync_history_query_command_supports_summary_only_text_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": "CHG-CLI-SUMMARY-ONLY",
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "closeout",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": ".governance/archive/CHG-CLI-SUMMARY-ONLY/sync-packet.yaml",
                    "headline": "首次同步",
                }],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--summary-by", "change_id",
                    "--summary-only",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("grouped summary by: change_id", output)
            self.assertIn("CHG-CLI-SUMMARY-ONLY", output)
            self.assertNotIn("[closeout/escalation]", output)

    def test_continuity_sync_history_query_command_supports_target_layer_grouped_summary_text_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-CLI-TARGET",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-CLI-TARGET/sync-packet.yaml",
                        "headline": "首次同步",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-CLI-TARGET",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-CLI-TARGET/sync-packet.yaml",
                        "headline": "二次同步",
                    },
                ],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--summary-by", "target_layer",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("grouped summary by: target_layer", output)
            self.assertIn("sponsor", output)
            self.assertIn("ops", output)

    def test_continuity_sync_history_query_text_grouped_summary_includes_latest_change_and_sync_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-CLI-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-CLI-A/sync-packet.yaml",
                        "headline": "首次同步",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-CLI-B",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-CLI-B/sync-packet.yaml",
                        "headline": "二次同步",
                    },
                ],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--summary-by", "target_layer",
                    "--summary-only",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("latest_change=CHG-CLI-B", output)
            self.assertIn("latest_sync_kind=routine-sync", output)

    def test_continuity_sync_history_query_text_grouped_summary_includes_distinct_change_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": "CHG-CLI-A",
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "closeout",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/archive/CHG-CLI-A/sync-packet.yaml",
                        "headline": "首次同步",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": "CHG-CLI-A",
                        "recorded_at": "2026-04-24T13:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-CLI-A/sync-packet.yaml",
                        "headline": "二次同步",
                    },
                    {
                        "event_id": "evt-3",
                        "change_id": "CHG-CLI-B",
                        "recorded_at": "2026-04-24T14:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": ".governance/changes/CHG-CLI-B/sync-packet.yaml",
                        "headline": "三次同步",
                    },
                ],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "sync-history-query",
                    "--month", "202604",
                    "--summary-by", "target_layer",
                    "--summary-only",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("distinct_changes=2", output)

    def test_continuity_digest_command_supports_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-DIGEST-JSON"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root),
                    "change", "create", change_id,
                    "--title", "Digest Json",
                ])

            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest json",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest json.\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "continuity", "handoff-package", "--change-id", change_id])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "digest",
                    "--format", "json",
                ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema"], "continuity-digest/v1")
            self.assertEqual(payload["change_id"], change_id)

    def test_continuity_digest_command_supports_text_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-DIGEST-TEXT"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)

            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
                "last_archive_at": "2026-04-24T12:00:00Z",
                "residual_followups": [],
            })
            write_yaml(root / ".governance/index/archive-map.yaml", {
                "schema": "archive-map/v1",
                "archives": [{
                    "change_id": change_id,
                    "archive_path": f".governance/archive/{change_id}/",
                    "archived_at": "2026-04-24T12:00:00Z",
                    "receipt": f".governance/archive/{change_id}/archive-receipt.yaml",
                }],
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "archived_at": "2026-04-24T12:00:00Z",
            })
            write_yaml(archive_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "Digest Text",
                "status": "archived",
                "current_step": 9,
            })
            write_yaml(archive_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
            })
            write_yaml(archive_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
            })
            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root),
                    "continuity", "closeout-packet",
                    "--change-id", change_id,
                    "--closeout-statement", "本轮已完成归档",
                    "--delivered-scope", "closeout-packet",
                    "--key-outcome", "done",
                    "--next-direction", "sync",
                    "--operator-summary", "digest text operator",
                    "--sponsor-summary", "digest text sponsor",
                ])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "digest",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Continuity digest:", output)
            self.assertIn(change_id, output)
            self.assertIn("recommended reading:", output)

    def test_continuity_digest_text_output_includes_recent_sync_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-DIGEST-SYNC"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root),
                    "change", "create", change_id,
                    "--title", "Digest Sync Text",
                ])

            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest sync text",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest sync text.\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "continuity", "handoff-package", "--change-id", change_id])

            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [{
                    "event_id": "evt-1",
                    "change_id": change_id,
                    "recorded_at": "2026-04-24T12:00:00Z",
                    "sync_kind": "escalation",
                    "source_kind": "increment",
                    "target_layer": "sponsor",
                    "target_scope": "project-level",
                    "packet_ref": f".governance/changes/{change_id}/sync-packet.yaml",
                    "headline": "需要更高层同步",
                }],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "digest",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("recent sync:", output)
            self.assertIn("需要更高层同步", output)

    def test_continuity_digest_text_output_includes_grouped_sync_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-DIGEST-SYNC-GROUPED"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root),
                    "change", "create", change_id,
                    "--title", "Digest Sync Grouped Text",
                ])

            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest sync grouped text",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest sync grouped text.\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "continuity", "handoff-package", "--change-id", change_id])

            history_dir = root / ".governance/runtime/sync-history"
            history_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(history_dir / "events-202604.yaml", {
                "schema": "sync-history/v1",
                "month": "202604",
                "events": [
                    {
                        "event_id": "evt-1",
                        "change_id": change_id,
                        "recorded_at": "2026-04-24T12:00:00Z",
                        "sync_kind": "routine-sync",
                        "source_kind": "increment",
                        "target_layer": "ops",
                        "target_scope": "project-level",
                        "packet_ref": f".governance/changes/{change_id}/sync-packet-ops.yaml",
                        "headline": "同步到 ops",
                    },
                    {
                        "event_id": "evt-2",
                        "change_id": change_id,
                        "recorded_at": "2026-04-24T12:10:00Z",
                        "sync_kind": "escalation",
                        "source_kind": "increment",
                        "target_layer": "sponsor",
                        "target_scope": "project-level",
                        "packet_ref": f".governance/changes/{change_id}/sync-packet-sponsor.yaml",
                        "headline": "同步到 sponsor",
                    },
                ],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "digest",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("recent sync groups:", output)
            self.assertIn("sponsor", output)
            self.assertIn("ops", output)

    def test_continuity_digest_text_output_includes_recent_runtime_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-DIGEST-RUNTIME"
            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)

            with contextlib.redirect_stdout(io.StringIO()):
                main([
                    "--root", str(root),
                    "change", "create", change_id,
                    "--title", "Digest Runtime Events",
                ])

            write_yaml(change_dir / "contract.yaml", {
                "objective": "digest runtime events text",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["DigestSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nDigest runtime events text.\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(root), "continuity", "handoff-package", "--change-id", change_id])

            timeline_dir = root / ".governance/runtime/timeline"
            timeline_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(timeline_dir / "events-202604.yaml", {
                "schema": "runtime-timeline/v1",
                "month": "202604",
                "events": [{
                    "schema": "runtime-event/v1",
                    "event_id": "evt-1",
                    "change_id": change_id,
                    "entity_type": "change",
                    "event_type": "review_completed",
                    "step": 8,
                    "from_status": "step7-verified",
                    "to_status": "review-approved",
                    "actor_id": "reviewer-agent",
                    "timestamp": "2026-04-24T12:00:00Z",
                    "refs": {"files": [f".governance/changes/{change_id}/review.yaml"]},
                }],
                "generated_at": "2026-04-24T12:00:00Z",
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "digest",
                    "--format", "text",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("recent events:", output)
            self.assertIn("review_completed -> review-approved", output)

    def test_continuity_export_sync_packet_command_materializes_external_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_root = root / "exports"
            ensure_governance_index(root)
            change_id = "CHG-CLI-EXP"
            archive_dir = root / f".governance/archive/{change_id}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(archive_dir / "sync-packet.yaml", {
                "schema": "sync-packet/v1",
                "change_id": change_id,
                "generated_at": "2026-04-24T12:00:00Z",
                "sync_kind": "escalation",
                "source_anchor": {"source_kind": "closeout"},
                "target_context": {"target_layer": "sponsor", "target_scope": "project-level"},
                "sync_summary": {"headline": "需要更高层同步"},
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "export-sync-packet",
                    "--change-id", change_id,
                    "--source-kind", "closeout",
                    "--output-dir", str(export_root),
                ])
            self.assertEqual(exit_code, 0)
            self.assertTrue((export_root / change_id / "sync-packet.yaml").exists())
            self.assertIn("Sync packet exported", stdout.getvalue())

    def test_continuity_owner_transfer_prepare_and_accept_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-OT"

            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "CLI owner transfer continuity",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent-a",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "emit owner transfer continuity from CLI",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["OwnerTransferContinuitySchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent-a", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nEmit owner transfer continuity from CLI.\n", encoding="utf-8")
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step7-verified",
                "current_change_id": change_id,
                "current_step": 7,
                "current_change": {
                    "change_id": change_id,
                    "status": "step7-verified",
                    "current_step": 7,
                },
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "step7-verified",
                "current_change_active": "step7-verified",
                "current_change_id": change_id,
                "last_archived_change": None,
                "last_archive_at": None,
                "residual_followups": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                prepare_exit = main([
                    "--root", str(root),
                    "continuity", "owner-transfer", "prepare",
                    "--change-id", change_id,
                    "--target-role", "reviewer",
                    "--outgoing-owner", "reviewer-agent-a",
                    "--incoming-owner", "reviewer-agent-b",
                    "--reason", "session handoff",
                    "--initiated-by", "maintainer-agent",
                ])
            self.assertEqual(prepare_exit, 0)
            self.assertIn("Owner transfer continuity written:", stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                accept_exit = main([
                    "--root", str(root),
                    "continuity", "owner-transfer", "accept",
                    "--change-id", change_id,
                    "--accepted-by", "reviewer-agent-b",
                    "--note", "accept handoff",
                ])
            self.assertEqual(accept_exit, 0)
            payload = load_yaml(root / f".governance/changes/{change_id}/owner-transfer-continuity.yaml")
            self.assertEqual(payload["acceptance"]["status"], "accepted")
            self.assertEqual(payload["acceptance"]["accepted_by"], "reviewer-agent-b")

    def test_continuity_increment_package_command_materializes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ensure_governance_index(root)
            change_id = "CHG-CLI-INCR"

            change_dir = root / f".governance/changes/{change_id}"
            change_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(change_dir / "manifest.yaml", {
                "change_id": change_id,
                "title": "CLI increment package",
                "status": "step7-verified",
                "current_step": 7,
                "roles": {
                    "executor": "executor-agent",
                    "verifier": "verifier-agent",
                    "reviewer": "reviewer-agent",
                },
            })
            write_yaml(change_dir / "contract.yaml", {
                "objective": "emit increment package from CLI",
                "scope_in": [".governance/**"],
                "scope_out": ["docs/**"],
                "allowed_actions": ["edit-governance-runtime"],
                "forbidden_actions": [
                    "no_truth_source_pollution",
                    "no_executor_reviewer_merge",
                    "no_executor_stable_write_authority",
                    "no_step6_before_step5_ready",
                ],
                "validation_objects": ["IncrementPackageSchema"],
                "verification": {"checks": ["state-consistency"], "commands": ["python3 -m unittest"]},
                "evidence_expectations": {"required": ["STEP_MATRIX_VIEW.md"]},
            })
            write_yaml(change_dir / "bindings.yaml", {
                "steps": {
                    "6": {"owner": "executor-agent", "gate": "auto-pass"},
                    "7": {"owner": "verifier-agent", "gate": "review-required"},
                    "8": {"owner": "reviewer-agent", "gate": "approval-required"},
                },
            })
            (change_dir / "tasks.md").write_text("# Tasks\n\nEmit increment package from CLI.\n", encoding="utf-8")
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "summary": {"status": "pass", "blocker_count": 0},
                "checks": [],
                "issues": [],
            })
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "step7-verified",
                "current_change_id": change_id,
                "current_step": 7,
                "current_change": {
                    "change_id": change_id,
                    "status": "step7-verified",
                    "current_step": 7,
                },
            })
            upsert_change_entry(root, {
                "change_id": change_id,
                "path": f".governance/changes/{change_id}",
                "status": "step7-verified",
                "current_step": 7,
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "step7-verified",
                "current_change_active": "step7-verified",
                "current_change_id": change_id,
                "last_archived_change": None,
                "last_archive_at": None,
                "residual_followups": [],
            })

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "continuity", "increment-package",
                    "--change-id", change_id,
                    "--reason", "post-verify update",
                    "--segment-owner", "verifier-agent",
                    "--segment-label", "verify-to-review",
                    "--new-finding", "runtime status schema 已稳定",
                    "--invalidated-assumption", "timeline 可以只靠生成式补写",
                    "--new-risk", "owner transfer 尚未进入 review trace",
                    "--blocker", "review gate still pending",
                    "--next-followup", "prepare review decision",
                ])

            self.assertEqual(exit_code, 0)
            self.assertIn("Increment package written:", stdout.getvalue())
            payload = load_yaml(root / f".governance/changes/{change_id}/increment-package.yaml")
            self.assertEqual(payload["increment_context"]["segment_label"], "verify-to-review")
            self.assertEqual(payload["delta"]["blockers"], ["review gate still pending"])


if __name__ == "__main__":
    unittest.main()
