from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import test_support  # noqa: F401

from governance.cli import main
from governance.index import ensure_governance_index
from governance.simple_yaml import load_yaml, write_yaml


class V039PreflightGuardTests(unittest.TestCase):
    def test_preflight_blocks_governed_project_without_active_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")

            output = self._run_cli(root, "preflight", "check", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertFalse(payload["can_execute"])
            self.assertEqual(payload["reason"], "no_active_change")
            self.assertIn("create or confirm a change package", payload["required_action"])

    def test_preflight_blocks_before_step5_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-BLOCKED", current_step=5, status="step5-prepared", step5_approved=False)

            output = self._run_cli(root, "preflight", "check", "--change-id", "CHG-V039-BLOCKED", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertFalse(payload["can_execute"])
            self.assertEqual(payload["reason"], "step5_approval_required")
            self.assertIn("Step 5 human gate approval", payload["required_action"])

    def test_preflight_allows_after_step5_approval_and_points_to_authoritative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-READY", current_step=5, status="step5-approved", step5_approved=True)

            output = self._run_cli(root, "preflight", "check", "--change-id", "CHG-V039-READY", "--format", "json")
            payload = json.loads(output)

            self.assertTrue(payload["can_execute"])
            self.assertEqual(payload["reason"], "ready_for_step6")
            self.assertEqual(payload["contract_ref"], ".governance/changes/CHG-V039-READY/contract.yaml")
            self.assertEqual(payload["evidence_ref"], ".governance/changes/CHG-V039-READY/evidence/")

    def test_preflight_blocks_baseline_required_change_without_digest_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            V039GovernanceAuditTests()._write_audited_change(
                root,
                "CHG-V039-PREFLIGHT-AUDIT",
                step5_note="approved baseline without digest",
            )

            output = self._run_cli(root, "preflight", "check", "--change-id", "CHG-V039-PREFLIGHT-AUDIT", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertFalse(payload["can_execute"])
            self.assertEqual(payload["reason"], "governance_audit_required")
            self.assertEqual(payload["audit_failures"][0]["name"], "step5_baseline_approval_binding")

    def test_preflight_checks_paths_against_contract_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-SCOPE", current_step=5, status="step5-approved", step5_approved=True)

            allowed = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                "foundation/components/Button.tsx",
                "--format",
                "json",
            ))
            outside = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                "src/outside.py",
                "--format",
                "json",
                expect=1,
            ))
            scope_out = json.loads(self._run_cli(
                root,
                "preflight",
                "check",
                "--change-id",
                "CHG-V039-SCOPE",
                "--path",
                ".governance/archive/CHG-X/file.yaml",
                "--format",
                "json",
                expect=1,
            ))

            self.assertTrue(allowed["can_execute"])
            self.assertEqual(outside["reason"], "scope_violation")
            self.assertEqual(outside["scope_violations"][0]["reason"], "outside_scope_in")
            self.assertEqual(scope_out["scope_violations"][0]["reason"], "matches_scope_out")

    def test_recovery_records_bypassed_flow_without_normal_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-RECOVERY", current_step=5, status="step5-prepared", step5_approved=False)

            self._run_cli(
                root,
                "preflight",
                "recovery",
                "--change-id",
                "CHG-V039-RECOVERY",
                "--reason",
                "Agent implemented before open-cowork preflight",
                "--modified",
                "foundation/components/Button.tsx",
                "--missing",
                "contract",
                "--missing",
                "evidence",
                "--missing",
                "review",
                "--action",
                "backfill change package as recovery only",
                "--recorded-by",
                "orchestrator-agent",
            )

            recovery = load_yaml(root / ".governance/changes/CHG-V039-RECOVERY/recovery/bypass-records.yaml")
            self.assertEqual(recovery["records"][0]["classification"], "flow_bypass_recovery")
            self.assertEqual(recovery["records"][0]["normal_evidence"], False)
            self.assertEqual(recovery["records"][0]["modified_files"], ["foundation/components/Button.tsx"])
            self.assertFalse((root / ".governance/changes/CHG-V039-RECOVERY/evidence/bypass-records.yaml").exists())

    def test_status_and_activate_show_execution_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-V039-STATUS", current_step=5, status="step5-prepared", step5_approved=False)

            status_output = self._run_cli(root, "status")
            activate_output = self._run_cli(root, "activate", "--change-id", "CHG-V039-STATUS")
            resume_output = self._run_cli(root, "resume", "--change-id", "CHG-V039-STATUS")

            self.assertIn("## Execution preflight", status_output)
            self.assertIn("can_modify_project_files: false", status_output)
            self.assertIn("Execution preflight:", activate_output)
            self.assertIn("can_modify_project_files: false", activate_output)
            self.assertIn("Execution preflight:", resume_output)
            self.assertIn("can_modify_project_files: false", resume_output)

    def test_step1_unconfirmed_does_not_materialize_future_step_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._run_cli(root, "init")
            self._run_cli(root, "change", "create", "CHG-V039-STEP1", "--title", "Step 1 boundary")
            self._run_cli(
                root,
                "change",
                "prepare",
                "CHG-V039-STEP1",
                "--goal",
                "Future reports must not exist before Step 1 confirmation",
                "--scope-in",
                "docs/**",
            )

            reports = sorted(path.name for path in (root / ".governance/changes/CHG-V039-STEP1/step-reports").glob("*"))
            self.assertEqual(reports, ["step-1.md", "step-1.yaml"])

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str, step5_approved: bool) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {
                "step6_entry_ready": step5_approved,
                "missing_items": [] if step5_approved else ["step5_approval"],
            },
            "target_validation_objects": ["foundation/components/**"],
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "Preflight guard",
            "scope_in": ["foundation/components/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files", "run_commands"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": ["foundation/components/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["v039"]},
            "evidence_expectations": {"required": ["test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "5": {"owner": "human-sponsor", "gate": "approval-required", "human_gate": True},
                "6": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False},
                "7": {"owner": "verifier-agent", "gate": "review-required", "human_gate": False},
                "8": {"owner": "reviewer-agent", "reviewer": "reviewer-agent", "gate": "approval-required", "human_gate": True},
            },
        })
        approvals = {}
        if step5_approved:
            approvals[5] = {"status": "approved", "approved_by": "human-sponsor"}
        write_yaml(change_dir / "human-gates.yaml", {"schema": "human-gates/v1", "change_id": change_id, "approvals": approvals})
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": {"change_id": change_id, "status": status, "current_step": current_step},
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {
            "schema": "changes-index/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/active-changes.yaml", {
            "schema": "active-changes/v1",
            "changes": [{"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}],
        })
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


class V039GovernanceAuditTests(unittest.TestCase):
    def test_audit_fails_when_baseline_digest_binding_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(root, "CHG-AUDIT-BASELINE", step5_note="approved baseline without digest")

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-BASELINE", "--format", "json", expect=1)
            payload = json.loads(output)

            self.assertEqual(payload["status"], "fail")
            check = self._check(payload, "step5_baseline_approval_binding")
            self.assertEqual(check["status"], "fail")
            self.assertIn("baseline digest", check["message"])

    def test_audit_accepts_canonical_baseline_with_digest_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-PASS",
                step5_note="APPROVED_BASELINE_DIGEST",
            )

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-PASS", "--format", "json")
            payload = json.loads(output)

            self.assertNotEqual(payload["status"], "fail")
            self.assertEqual(self._check(payload, "baseline_canonical_artifact")["status"], "pass")
            self.assertEqual(self._check(payload, "step5_baseline_approval_binding")["status"], "pass")

    def test_audit_fails_when_required_step_output_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-EMPTY-DESIGN",
                current_step=5,
                status="step5-approved",
                step5_note="APPROVED_BASELINE_DIGEST",
            )
            (root / ".governance/changes/CHG-AUDIT-EMPTY-DESIGN/design.md").write_text("TODO\n", encoding="utf-8")

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-EMPTY-DESIGN", "--format", "json", expect=1)
            payload = json.loads(output)

            check = self._check(payload, "step_3_required_output")
            self.assertEqual(check["status"], "fail")
            self.assertIn("empty or template-like", check["message"])

    def test_archive_blocks_unresolved_flow_bypass_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-RECOVERY",
                current_step=8,
                status="review-approved",
                step5_note="APPROVED_BASELINE_DIGEST",
                with_review=True,
                archive_gates=True,
            )
            self._run_cli(
                root,
                "preflight",
                "recovery",
                "--change-id",
                "CHG-AUDIT-RECOVERY",
                "--reason",
                "implemented before preflight",
                "--modified",
                "src/governance/cli.py",
                "--missing",
                "evidence",
                "--action",
                "review as exceptional recovery",
                "--recorded-by",
                "orchestrator-agent",
            )

            output = self._run_cli(root, "archive", "--change-id", "CHG-AUDIT-RECOVERY", expect=1)

            self.assertIn("governance audit did not pass", output)
            self.assertIn("flow_bypass_recovery", output)
            self.assertFalse((root / ".governance/archive/CHG-AUDIT-RECOVERY/archive-receipt.yaml").exists())

    def test_audit_reads_step9_required_output_from_archive_for_archived_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_id = "CHG-AUDIT-ARCHIVED"
            self._write_audited_change(
                root,
                change_id,
                current_step=9,
                status="archived",
                step5_note="APPROVED_BASELINE_DIGEST",
                with_review=True,
                archive_gates=True,
            )
            change_dir = root / ".governance/changes" / change_id
            archive_dir = root / ".governance/archive" / change_id
            shutil.copytree(change_dir, archive_dir)
            review = load_yaml(archive_dir / "review.yaml")
            review["writer"] = {"tool": "ocw review", "source": "governance.review.write_review_decision"}
            write_yaml(archive_dir / "review.yaml", review)
            write_yaml(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml", {
                "schema": "governance/final-state-consistency-check/v1",
                "change_id": change_id,
                "status": "pass",
            })
            write_yaml(archive_dir / "archive-receipt.yaml", {
                "schema": "archive-receipt/v1",
                "change_id": change_id,
                "archive_executed": True,
                "traceability": {
                    "final_round_report": f".governance/archive/{change_id}/FINAL_ROUND_REPORT.md",
                    "final_state_consistency": f".governance/archive/{change_id}/FINAL_STATE_CONSISTENCY_CHECK.yaml",
                },
            })
            (archive_dir / "FINAL_ROUND_REPORT.md").write_text(
                f"# 最终闭环报告：{change_id}\n\n## 初始需求\nArchived requirement.\n\n## 最终结论\n- 是否归档：是\n\n## 四阶段九步过程简报\nArchived final report.\n",
                encoding="utf-8",
            )
            write_yaml(root / ".governance/index/current-change.yaml", {
                "schema": "current-change/v1",
                "status": "idle",
                "current_change_id": None,
                "current_step": None,
                "current_change": {"change_id": None, "status": "idle", "current_step": None},
            })
            write_yaml(root / ".governance/index/maintenance-status.yaml", {
                "schema": "maintenance-status/v1",
                "status": "idle",
                "current_change_active": "none",
                "current_change_id": None,
                "last_archived_change": change_id,
            })

            output = self._run_cli(root, "audit", "--change-id", change_id, "--format", "json")
            payload = json.loads(output)

            self.assertNotEqual(payload["status"], "fail")
            self.assertEqual(self._check(payload, "state_consistency")["status"], "pass")
            self.assertEqual(self._check(payload, "step_9_required_output")["status"], "pass")
            self.assertIn(".governance/archive", self._check(payload, "step_9_required_output")["ref"])

    def test_verify_blocks_fail_level_audit_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-VERIFY",
                status="step6-executed-pre-step7",
                step5_note="approved baseline without digest",
            )
            evidence_dir = root / ".governance/changes/CHG-AUDIT-VERIFY/evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(evidence_dir / "execution-summary.yaml", {"schema": "execution-summary/v1", "status": "completed"})

            output = self._run_cli(root, "verify", "--change-id", "CHG-AUDIT-VERIFY", expect=1)

            self.assertIn("fail-level governance audit findings", output)

    def test_review_blocks_fail_level_audit_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-REVIEW",
                current_step=7,
                status="step7-verified",
                step5_note="approved baseline without digest",
            )
            write_yaml(root / ".governance/changes/CHG-AUDIT-REVIEW/verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": "CHG-AUDIT-REVIEW",
                "summary": {"status": "pass"},
            })

            output = self._run_cli(
                root,
                "review",
                "--change-id",
                "CHG-AUDIT-REVIEW",
                "--decision",
                "approve",
                "--reviewer",
                "reviewer-agent",
                expect=1,
            )

            self.assertIn("fail-level governance audit findings", output)

    def test_verify_and_review_write_canonical_markdown_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-REPORTS",
                status="step6-executed-pre-step7",
                step5_note="APPROVED_BASELINE_DIGEST",
            )
            evidence_dir = root / ".governance/changes/CHG-AUDIT-REPORTS/evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(evidence_dir / "execution-summary.yaml", {"schema": "execution-summary/v1", "status": "completed"})

            self._run_cli(root, "verify", "--change-id", "CHG-AUDIT-REPORTS")
            verify_report = root / ".governance/changes/CHG-AUDIT-REPORTS/VERIFY_REPORT.md"
            self.assertTrue(verify_report.exists())
            self.assertIn("canonical_artifact: true", verify_report.read_text(encoding="utf-8"))

            self._run_cli(
                root,
                "review",
                "--change-id",
                "CHG-AUDIT-REPORTS",
                "--decision",
                "approve",
                "--reviewer",
                "reviewer-agent",
                "--rationale",
                "ready",
            )
            review_report = root / ".governance/changes/CHG-AUDIT-REPORTS/REVIEW_REPORT.md"
            self.assertTrue(review_report.exists())
            self.assertIn("source_facts: review.yaml", review_report.read_text(encoding="utf-8"))

    def test_audit_reconciles_acknowledgement_that_became_human_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(root, "CHG-AUDIT-GATE-ACK", step5_note="APPROVED_BASELINE_DIGEST")
            gates_path = root / ".governance/changes/CHG-AUDIT-GATE-ACK/human-gates.yaml"
            gates = load_yaml(gates_path)
            gates["acknowledgements"] = [{"step": 4, "status": "acknowledged", "acknowledged_by": "human-sponsor"}]
            write_yaml(gates_path, gates)
            bindings_path = root / ".governance/changes/CHG-AUDIT-GATE-ACK/bindings.yaml"
            bindings = load_yaml(bindings_path)
            bindings["steps"]["4"] = {"owner": "human-sponsor", "human_gate": True}
            write_yaml(bindings_path, bindings)

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-GATE-ACK", "--format", "json", expect=1)
            payload = json.loads(output)

            check = self._check(payload, "human_gate_reconciliation")
            self.assertEqual(check["status"], "fail")
            self.assertIn("acknowledgement exists", check["message"])

    def test_audit_fails_manual_review_without_writer_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-MANUAL-REVIEW",
                current_step=8,
                status="review-approved",
                step5_note="APPROVED_BASELINE_DIGEST",
                with_review=True,
            )

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-MANUAL-REVIEW", "--format", "json", expect=1)
            payload = json.loads(output)

            check = self._check(payload, "writer_metadata")
            self.assertEqual(check["status"], "fail")
            self.assertIn("review.yaml", check["message"])

    def test_audit_fails_canonical_report_source_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(
                root,
                "CHG-AUDIT-DIGEST-MISMATCH",
                current_step=7,
                status="step7-verified",
                step5_note="APPROVED_BASELINE_DIGEST",
            )
            report = root / ".governance/changes/CHG-AUDIT-DIGEST-MISMATCH/VERIFY_REPORT.md"
            report.write_text(
                "---\nschema: verify-report/v1\ncanonical_artifact: true\nsource_facts: verify.yaml\nsource_digest: sha256:"
                + "0" * 64
                + "\n---\n\n# Verify\n\nVerification completed.\n",
                encoding="utf-8",
            )

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-DIGEST-MISMATCH", "--format", "json", expect=1)
            payload = json.loads(output)

            check = self._check(payload, "canonical_artifact_consistency")
            self.assertEqual(check["status"], "fail")
            self.assertIn("source_digest mismatch", check["message"])

    def test_audit_fails_malformed_project_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(root, "CHG-AUDIT-RULE", step5_note="APPROVED_BASELINE_DIGEST")
            policy_dir = root / ".governance/policies"
            policy_dir.mkdir(parents=True, exist_ok=True)
            write_yaml(policy_dir / "rules.yaml", {"rules": [{"id": "project-rule-without-fallback", "applies_to_steps": [7], "severity": "blocking", "evidence_required": ["audit"]}]})

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-RULE", "--format", "json", expect=1)
            payload = json.loads(output)

            check = self._check(payload, "rule_sources")
            self.assertEqual(check["status"], "fail")
            self.assertIn("project-rule-without-fallback", check["message"])

    def test_scope_violation_requires_explicit_scope_expansion_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_audited_change(root, "CHG-AUDIT-SCOPE", step5_note="APPROVED_BASELINE_DIGEST")
            evidence_dir = root / ".governance/changes/CHG-AUDIT-SCOPE/evidence"
            write_yaml(evidence_dir / "changed-files-manifest.yaml", {
                "schema": "changed-files-manifest/v1",
                "files": ["src/governance/audit.py", ".governance/changes/CHG-AUDIT-SCOPE/tasks.md"],
            })

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-SCOPE", "--format", "json", expect=1)
            payload = json.loads(output)
            self.assertEqual(self._check(payload, "changed_files_scope")["status"], "fail")

            write_yaml(evidence_dir / "scope-expansion-approval.yaml", {
                "schema": "scope-expansion-approval/v1",
                "change_id": "CHG-AUDIT-SCOPE",
                "approved_by": "human-sponsor",
                "approved_paths": [".governance/changes/CHG-AUDIT-SCOPE/tasks.md"],
                "approval_text": "Human explicitly asked the executor to complete all task items.",
            })

            output = self._run_cli(root, "audit", "--change-id", "CHG-AUDIT-SCOPE", "--format", "json")
            payload = json.loads(output)
            self.assertEqual(self._check(payload, "changed_files_scope")["status"], "pass")

    def _write_audited_change(
        self,
        root: Path,
        change_id: str,
        *,
        current_step: int = 6,
        status: str = "step6-in-progress",
        step5_note: str,
        with_review: bool = False,
        archive_gates: bool = False,
    ) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        (change_dir / "step-reports").mkdir(parents=True, exist_ok=True)
        (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
        for step in range(1, current_step + 1):
            (change_dir / f"step-reports/step-{step}.md").write_text(f"# Step {step}\n\nMaterialized output.\n", encoding="utf-8")
        (change_dir / "BASELINE_REVIEW.md").write_text(
            "---\nschema: baseline-review/v1\ncanonical_artifact: true\n---\n\n# Baseline\n\nReviewable baseline.\n",
            encoding="utf-8",
        )
        baseline_digest = hashlib.sha256((change_dir / "BASELINE_REVIEW.md").read_bytes()).hexdigest()
        if step5_note == "APPROVED_BASELINE_DIGEST":
            step5_note = f"Approved BASELINE_REVIEW.md digest sha256:{baseline_digest} for Step 6 authority."
        (change_dir / "intent-confirmation.yaml").write_text("schema: intent-confirmation/v1\nstatus: confirmed\n", encoding="utf-8")
        (change_dir / "requirements.md").write_text("# Requirements\n\nReviewable requirements for audit coverage.\n", encoding="utf-8")
        (change_dir / "design.md").write_text("# Design\n\nReviewable design for audit coverage.\n", encoding="utf-8")
        (change_dir / "tasks.md").write_text("# Tasks\n\nReviewable tasks for audit coverage.\n", encoding="utf-8")
        if current_step >= 6:
            write_yaml(change_dir / "evidence/execution-summary.yaml", {"schema": "execution-summary/v1", "status": "completed"})
        if current_step >= 7:
            write_yaml(change_dir / "verify.yaml", {
                "schema": "verify-result/v1",
                "change_id": change_id,
                "writer": {
                    "tool": "ocw verify",
                    "canonical_artifact": "VERIFY_REPORT.md",
                    "source": "governance.verify.write_verify_result",
                },
                "summary": {"status": "pass"},
            })
            (change_dir / "VERIFY_REPORT.md").write_text(
                "---\nschema: verify-report/v1\ncanonical_artifact: true\nsource_facts: verify.yaml\n---\n\n# Verify\n\nVerification completed.\n",
                encoding="utf-8",
            )
        if current_step >= 8:
            (change_dir / "REVIEW_REPORT.md").write_text(
                "---\nschema: review-report/v1\ncanonical_artifact: true\n---\n\n# Review\n\nReview completed.\n",
                encoding="utf-8",
            )
        validation_objects = ["src/governance/**", "tests/**", f".governance/changes/{change_id}/BASELINE_REVIEW.md"]
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {"step6_entry_ready": True, "missing_items": []},
            "target_validation_objects": validation_objects,
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "Audit governance invariants",
            "scope_in": ["src/governance/**", "tests/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files", "run_commands"],
            "forbidden_actions": [
                "no_truth_source_pollution",
                "no_executor_reviewer_merge",
                "no_executor_stable_write_authority",
                "no_step6_before_step5_ready",
            ],
            "validation_objects": validation_objects,
            "verification": {"commands": ["python3 -m unittest"], "checks": ["audit"]},
            "evidence_expectations": {"required": ["baseline_review"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "6": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False},
                "7": {"owner": "verifier-agent", "gate": "review-required", "human_gate": False},
                "8": {"owner": "reviewer-agent", "reviewer": "reviewer-agent", "gate": "approval-required", "human_gate": True},
            },
        })
        approvals = {
            5: {"status": "approved", "approved_by": "human-sponsor", "note": step5_note},
        }
        if archive_gates:
            approvals[8] = {"status": "approved", "approved_by": "human-sponsor"}
            approvals[9] = {"status": "approved", "approved_by": "human-sponsor"}
        write_yaml(change_dir / "human-gates.yaml", {"schema": "human-gates/v1", "change_id": change_id, "approvals": approvals})
        if with_review:
            write_yaml(change_dir / "review.yaml", {
                "schema": "review-decision/v1",
                "change_id": change_id,
                "decision": {"status": "approve"},
                "reviewers": [{"role": "reviewer", "id": "reviewer-agent"}],
                "trace": {"evidence_refs": [], "verify_refs": ["verify.yaml"]},
            })
        self._write_indexes(root, change_id, current_step, status)

    def _write_indexes(self, root: Path, change_id: str, current_step: int, status: str) -> None:
        entry = {"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step}
        write_yaml(root / ".governance/index/current-change.yaml", {
            "schema": "current-change/v1",
            "status": status,
            "current_change_id": change_id,
            "current_step": current_step,
            "current_change": entry,
        })
        write_yaml(root / ".governance/index/changes-index.yaml", {"schema": "changes-index/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/active-changes.yaml", {"schema": "active-changes/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/maintenance-status.yaml", {
            "schema": "maintenance-status/v1",
            "status": status,
            "current_change_active": status,
            "current_change_id": change_id,
        })

    def _check(self, payload: dict, name: str) -> dict:
        return next(item for item in payload["checks"] if item["name"] == name)

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


class V039TeamOperatingLoopTests(unittest.TestCase):
    def test_participant_discover_register_assign_and_team_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-TEAM", current_step=6, status="step6-in-progress")

            self._run_cli(root, "participant", "discover", "--recorded-by", "codex-agent")
            self._run_cli(
                root,
                "participant",
                "register",
                "--participant-id",
                "remote-reviewer",
                "--type",
                "agent",
                "--domain",
                "team-remote",
                "--entrypoint",
                "declared-invite://remote-reviewer",
                "--capability",
                "review",
                "--default-role",
                "reviewer",
                "--step",
                "8",
                "--remote",
                "--recorded-by",
                "human-sponsor",
            )
            self._run_cli(root, "participant", "assign", "--participant-id", "codex-agent", "--change-id", "CHG-TEAM", "--step", "6", "--role", "executor", "--recorded-by", "human-sponsor")
            self._run_cli(root, "assignment", "set", "--change-id", "CHG-TEAM", "--step", "8", "--role", "reviewer", "--actor", "remote-reviewer", "--recorded-by", "human-sponsor")

            status = self._run_cli(root, "team", "status", "--format", "json")
            payload = json.loads(status)

            participants = load_yaml(root / ".governance/team/participants.yaml")
            assignments = load_yaml(root / ".governance/team/assignments.yaml")
            self.assertIn("discovered_candidates", participants)
            self.assertEqual(participants["participants"][0]["domain"], "team-remote")
            self.assertTrue(participants["participants"][0]["human_confirmed"])
            self.assertEqual(participants["participants"][0]["review_status"], "human-confirmed")
            self.assertEqual(assignments["assignments"][0]["role"], "executor")
            self.assertEqual(assignments["assignments"][1]["actor"], "remote-reviewer")
            self.assertEqual(payload["active_changes"][0]["executor"], "codex-agent")
            self.assertEqual(payload["active_changes"][0]["reviewer"], "remote-reviewer")

    def test_agent_recorded_participant_registration_remains_pending_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-PARTICIPANT", current_step=1, status="step1-ready")

            self._run_cli(
                root,
                "participant",
                "register",
                "--participant-id",
                "agent-registered",
                "--type",
                "agent",
                "--domain",
                "personal-local",
                "--entrypoint",
                "codex",
                "--capability",
                "execute",
                "--default-role",
                "executor",
                "--step",
                "6",
                "--recorded-by",
                "codex-agent",
            )

            participants = load_yaml(root / ".governance/team/participants.yaml")
            item = participants["participants"][0]
            self.assertFalse(item["human_confirmed"])
            self.assertEqual(item["review_status"], "pending-human-review")
            self.assertNotIn("confirmed_by", item)

    def test_assignment_blocks_reviewer_self_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-SELF", current_step=6, status="step6-in-progress")

            self._run_cli(root, "assignment", "set", "--change-id", "CHG-SELF", "--step", "6", "--role", "executor", "--actor", "same-agent", "--recorded-by", "human-sponsor")
            output = self._run_cli(
                root,
                "assignment",
                "set",
                "--change-id",
                "CHG-SELF",
                "--step",
                "8",
                "--role",
                "reviewer",
                "--actor",
                "same-agent",
                "--recorded-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("reviewer cannot review their own execution", output)

    def test_assignment_blocks_reviewer_self_review_from_existing_bindings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-BINDING-SELF", current_step=6, status="step6-in-progress")
            bindings_path = root / ".governance/changes/CHG-BINDING-SELF/bindings.yaml"
            bindings = load_yaml(bindings_path)
            step6 = bindings["steps"].get("6") or bindings["steps"].get(6) or bindings["steps"].get("'6'")
            step6["executor"] = "same-agent"
            step6["owner"] = "same-agent"
            write_yaml(bindings_path, bindings)

            output = self._run_cli(
                root,
                "assignment",
                "set",
                "--change-id",
                "CHG-BINDING-SELF",
                "--step",
                "8",
                "--role",
                "reviewer",
                "--actor",
                "same-agent",
                "--recorded-by",
                "human-sponsor",
                expect=1,
            )

            self.assertIn("reviewer cannot review their own execution", output)

    def test_blocked_reviewer_queue_digest_carry_forward_and_retrospective(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-OPS", current_step=7, status="step7-verified")

            self._run_cli(root, "blocked", "set", "--change-id", "CHG-OPS", "--reason", "Need review", "--waiting-on", "reviewer", "--next-decision", "Assign reviewer", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "reviewer", "queue", "--change-id", "CHG-OPS", "--reviewer", "independent-reviewer", "--priority", "high", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "carry-forward", "add", "--item-id", "follow-up-1", "--summary", "Improve team digest", "--source-change-id", "CHG-OPS", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "retrospective", "add", "--retrospective-id", "retro-1", "--change-id", "CHG-OPS", "--summary", "Loop worked", "--learning", "Keep gates visible", "--recorded-by", "maintainer-agent")

            digest = json.loads(self._run_cli(root, "team", "digest", "--format", "json"))

            self.assertEqual(digest["blocked"][0]["change_id"], "CHG-OPS")
            self.assertEqual(digest["reviewer_queue"][0]["priority"], "high")
            self.assertEqual(digest["carry_forward"][0]["id"], "follow-up-1")
            self.assertEqual(digest["retrospectives"][0]["id"], "retro-1")
            self.assertTrue((root / ".governance/team/retrospectives/retro-1.md").exists())

    def test_recurring_intent_and_carry_forward_promote_only_create_step1_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_active_change(root, "CHG-CURRENT", current_step=5, status="step5-prepared")

            self._run_cli(root, "recurring-intent", "add", "--intent-id", "weekly-sync", "--summary", "Weekly governance sync", "--cadence", "weekly", "--recorded-by", "human-sponsor")
            trigger = json.loads(self._run_cli(root, "recurring-intent", "trigger", "--intent-id", "weekly-sync", "--change-id", "CHG-WEEKLY", "--recorded-by", "orchestrator-agent", "--format", "json"))
            self._run_cli(root, "carry-forward", "add", "--item-id", "cf-1", "--summary", "Next loop item", "--source-change-id", "CHG-CURRENT", "--recorded-by", "orchestrator-agent")
            self._run_cli(root, "carry-forward", "promote", "--item-id", "cf-1", "--change-id", "CHG-CF", "--recorded-by", "orchestrator-agent")

            weekly_manifest = load_yaml(root / ".governance/changes/CHG-WEEKLY/manifest.yaml")
            cf_manifest = load_yaml(root / ".governance/changes/CHG-CF/manifest.yaml")
            self.assertEqual(trigger["current_step"], 1)
            self.assertEqual(weekly_manifest["current_step"], 1)
            self.assertEqual(weekly_manifest["status"], "awaiting-intent-confirmation")
            self.assertEqual(cf_manifest["current_step"], 1)
            self.assertNotEqual(cf_manifest["status"], "step6-in-progress")

    def _write_active_change(self, root: Path, change_id: str, *, current_step: int, status: str) -> None:
        ensure_governance_index(root)
        change_dir = root / ".governance/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        write_yaml(change_dir / "manifest.yaml", {
            "change_id": change_id,
            "title": change_id,
            "status": status,
            "current_step": current_step,
            "readiness": {"step6_entry_ready": current_step >= 6, "missing_items": []},
        })
        write_yaml(change_dir / "contract.yaml", {
            "change_id": change_id,
            "objective": "Team loop",
            "scope_in": ["src/**"],
            "scope_out": [".governance/archive/**"],
            "allowed_actions": ["edit_files"],
            "forbidden_actions": ["self_review"],
            "validation_objects": ["src/**"],
            "verification": {"commands": ["python3 -m unittest"], "checks": ["team loop"]},
            "evidence_expectations": {"required": ["test_output"]},
        })
        write_yaml(change_dir / "bindings.yaml", {
            "steps": {
                "6": {"owner": "executor-agent", "reviewer": "verifier-agent", "human_gate": False},
                "8": {"owner": "independent-reviewer", "reviewer": "independent-reviewer", "human_gate": True},
            }
        })
        write_yaml(change_dir / "verify.yaml", {"status": "pending"})
        write_yaml(change_dir / "review.yaml", {"decision": {"status": "pending"}})
        entry = {"change_id": change_id, "path": f".governance/changes/{change_id}", "status": status, "current_step": current_step, "title": change_id}
        write_yaml(root / ".governance/index/current-change.yaml", {"schema": "current-change/v1", "status": status, "current_change_id": change_id, "current_step": current_step, "current_change": entry})
        write_yaml(root / ".governance/index/changes-index.yaml", {"schema": "changes-index/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/active-changes.yaml", {"schema": "active-changes/v1", "changes": [entry]})
        write_yaml(root / ".governance/index/maintenance-status.yaml", {"schema": "maintenance-status/v1", "status": status, "current_change_active": status, "current_change_id": change_id})

    def _run_cli(self, root: Path, *args: str, expect: int = 0) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--root", str(root), *args])
        output = stdout.getvalue()
        self.assertEqual(exit_code, expect, output)
        return output


if __name__ == "__main__":
    unittest.main()
