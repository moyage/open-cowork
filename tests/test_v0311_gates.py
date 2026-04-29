from __future__ import annotations

import unittest

import test_support  # noqa: F401

from governance.lean_round import (
    evaluate_closeout_gate,
    evaluate_execution_gate,
    evaluate_gate_decision,
    status_gate_decision,
)
from governance.lean_state import initial_lean_state


class V0311GateTests(unittest.TestCase):
    def test_execution_gate_blocks_without_participant_initialization(self):
        state = initial_lean_state(round_id="R-GATE-001", goal="缺协作者初始化")
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"

        decision = evaluate_execution_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "participant_initialization_required")

    def test_execution_gate_blocks_approval_without_evidence_ref(self):
        state = _state_ready_for_execution()
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approved_by"] = "human:mlabs"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = ""

        decision = evaluate_execution_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "approval_evidence_required")

    def test_execution_gate_blocks_self_review_without_bypass_evidence(self):
        state = _state_ready_for_execution()
        state["active_round"]["participants"]["executor"] = "codex"
        state["active_round"]["participants"]["reviewer"] = "codex"
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"

        decision = evaluate_execution_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "independent_reviewer_required")

    def test_execution_gate_blocks_missing_executor_even_when_status_claims_complete(self):
        state = _state_ready_for_execution()
        state["active_round"]["participants"]["executor"] = ""
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"

        decision = evaluate_execution_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "participant_role_required")

    def test_execution_gate_blocks_missing_reviewer_even_when_status_claims_complete(self):
        state = _state_ready_for_execution()
        state["active_round"]["participants"]["reviewer"] = ""
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"

        decision = evaluate_execution_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "participant_role_required")

    def test_execution_gate_allows_initialized_participants_and_evidence_backed_approval(self):
        state = _state_ready_for_execution()
        state["active_round"]["gates"]["execution"]["status"] = "approved"
        state["active_round"]["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"

        decision = evaluate_execution_gate(state)

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "execution_ready")

    def test_closeout_blocks_open_blocking_decision(self):
        state = _state_ready_for_closeout()
        state["decision_needed"].append({
            "id": "D-001",
            "status": "open",
            "summary": "需要人确认范围",
            "requested_by": "codex",
            "created_at": "2026-04-29",
            "blocking": True,
            "resolved_by": "",
            "resolved_at": "",
            "resolution_summary": "",
            "evidence_ref": "",
        })

        decision = evaluate_closeout_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "blocking_decision_open")

    def test_closeout_blocks_review_revise(self):
        state = _state_ready_for_closeout()
        state["active_round"]["review"]["decision"] = "revise"

        decision = evaluate_closeout_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "review_approval_required")

    def test_closeout_allows_verified_approved_review_and_closeout_gate(self):
        state = _state_ready_for_closeout()

        decision = evaluate_closeout_gate(state)

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "closeout_ready")

    def test_closeout_accepts_passed_verify_status(self):
        state = _state_ready_for_closeout()
        state["active_round"]["verify"]["status"] = "passed"

        decision = evaluate_closeout_gate(state)

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "closeout_ready")

    def test_closeout_blocks_failed_blocking_external_rule(self):
        state = _state_ready_for_closeout()
        state["active_round"]["external_rules"]["active"] = [
            {"id": "review-lint", "failure_impact": "blocking"},
            {"id": "style-note", "failure_impact": "warning"},
        ]
        state["active_round"]["verify"]["rule_results"] = [
            {"rule_id": "review-lint", "status": "fail", "summary": "lint failed"},
            {"rule_id": "style-note", "status": "fail", "summary": "warning only"},
        ]

        decision = evaluate_closeout_gate(state)

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "blocking_rule_failed")
        self.assertEqual(decision["rule_id"], "review-lint")

    def test_closeout_tolerates_legacy_string_external_rules(self):
        state = _state_ready_for_closeout()
        state["active_round"]["external_rules"]["active"] = [
            "scope-bound-execution",
            "compact-evidence-only",
        ]

        decision = evaluate_closeout_gate(state)

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "closeout_ready")

    def test_gate_decision_is_shared_across_entrypoints(self):
        state = _state_ready_for_closeout()

        shared = evaluate_gate_decision(state, "closeout")
        status_view = status_gate_decision(state, "closeout")

        self.assertEqual(shared, status_view)


def _state_ready_for_execution() -> dict:
    state = initial_lean_state(round_id="R-GATE-READY", goal="执行 gate")
    active_round = state["active_round"]
    active_round["phase"] = "plan-contract"
    active_round["participants"]["sponsor"] = "human:mlabs"
    active_round["participants"]["owner_agent"] = "codex"
    active_round["participants"]["executor"] = "codex"
    active_round["participants"]["reviewer"] = "hermes"
    active_round["participant_initialization"]["status"] = "complete"
    active_round["participant_initialization"]["initialized_roles"] = ["sponsor", "owner_agent", "executor", "reviewer"]
    active_round["participant_initialization"]["missing_roles"] = []
    active_round["participant_initialization"]["role_bindings"] = [
        {
            "role": "executor",
            "actor": "codex",
            "responsibility": "完整实现 scope in",
            "authority_scope": ["src/governance/**", "tests/**"],
            "output_responsibility": ["code", "tests"],
            "independence_requirement": "不能批准最终 review",
            "evidence_ref": "E-ROLE-001",
        },
        {
            "role": "reviewer",
            "actor": "hermes",
            "responsibility": "独立 review",
            "authority_scope": ["review"],
            "output_responsibility": ["review decision"],
            "independence_requirement": "必须独立于 executor",
            "evidence_ref": "E-ROLE-002",
        },
    ]
    return state


def _state_ready_for_closeout() -> dict:
    state = _state_ready_for_execution()
    active_round = state["active_round"]
    active_round["phase"] = "verify-review"
    active_round["gates"]["execution"]["status"] = "approved"
    active_round["gates"]["execution"]["approval_evidence_ref"] = "E-APPROVAL-001"
    active_round["verify"]["status"] = "pass"
    active_round["review"]["status"] = "completed"
    active_round["review"]["decision"] = "approve"
    active_round["review"]["reviewer"] = "hermes"
    active_round["gates"]["closeout"]["status"] = "approved"
    active_round["gates"]["closeout"]["approval_evidence_ref"] = "E-CLOSEOUT-001"
    active_round["closeout"]["summary"] = "完成"
    return state


if __name__ == "__main__":
    unittest.main()
