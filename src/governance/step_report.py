from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package
from .contract import ContractValidationError
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import (
    ACTION_PURPOSES,
    PHASE_LABELS,
    STEP_LABELS,
    _approval_state_for_step,
    _gate_state_for_step,
    _gate_type_for_step,
    render_step_matrix,
)


def materialize_step_report(root: str | Path, *, change_id: str, step: int | None = None) -> dict:
    package = read_change_package(root, change_id)
    intent = _load_optional_yaml(package.path / "intent-confirmation.yaml")
    contract = _load_optional_yaml(package.path / "contract.yaml")
    try:
        matrix = render_step_matrix(root, change_id)
    except ContractValidationError:
        if step not in {1, 2} or not intent:
            raise
        matrix = _early_intent_matrix(package.manifest)
    selected_step = step or matrix["current_step"]
    if not isinstance(selected_step, int) or selected_step < 1 or selected_step > 9:
        raise ValueError("step must be an integer from 1 to 9")
    bindings = _load_optional_yaml(package.path / "bindings.yaml")
    human_gates = _load_optional_yaml(package.path / "human-gates.yaml")
    step_binding = _step_binding(bindings, selected_step)
    approval = _approval_for_step(human_gates, selected_step)
    gate_type = _gate_type_for_step(selected_step, step_binding)
    gate_state = _gate_state_for_step(selected_step, matrix["current_step"], gate_type, approval)
    approval_state = _approval_state_for_step(gate_type, approval)
    payload = {
        "schema": "step-report/v1",
        "change_id": change_id,
        "step": selected_step,
        "standard_step": f"Step {selected_step} / {STEP_LABELS[selected_step]}",
        "traditional_mapping": PHASE_LABELS[_phase_index(selected_step)],
        "phase": PHASE_LABELS[_phase_index(selected_step)],
        "label": STEP_LABELS[selected_step],
        "status": _status_for_step(selected_step, matrix),
        "owner": step_binding.get("owner") or matrix.get("current_owner_or_stage_actor"),
        "assistants": step_binding.get("assistants", []),
        "reviewer": step_binding.get("reviewer"),
        "human_gate": bool(step_binding.get("human_gate")),
        "gate_type": gate_type,
        "gate_state": gate_state,
        "approval_state": approval_state,
        "participant_responsibilities": _participant_responsibilities(step_binding),
        "objective": ACTION_PURPOSES[selected_step],
        "inputs": _inputs_for_step(selected_step, change_id),
        "outputs": _outputs_for_step(selected_step, change_id),
        "intent_summary": _intent_summary(intent, contract),
        "artifact_summary": _artifact_summary(package.path, selected_step),
        "evidence": _evidence_summary(package.path, selected_step),
        "review_gate_vs_decision": _review_gate_vs_decision(package.path, approval_state, gate_state) if selected_step == 8 else {},
        "done_criteria": _done_criteria(selected_step, intent),
        "next_entry_criteria": _next_entry_criteria(selected_step),
        "blockers": matrix.get("blockers", []),
        "framework_controls": _framework_controls(selected_step, gate_type),
        "agent_actions_done": _agent_actions_done(selected_step, package.path),
        "agent_actions_expected": _agent_actions_expected(selected_step, step_binding, payload_status := _status_for_step(selected_step, matrix), approval_state),
        "human_decisions_required": _human_decisions(selected_step, step_binding, intent),
        "human_confirmation_options": _human_confirmation_options(step_binding),
        "recommended_next_action": _recommended_next_action(selected_step, step_binding, intent, payload_status, approval_state),
        "generated_at": _now_utc(),
    }
    report_dir = package.path / "step-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(report_dir / f"step-{selected_step}.yaml", payload)
    (report_dir / f"step-{selected_step}.md").write_text(_format_report(payload), encoding="utf-8")
    return payload


def _early_intent_matrix(manifest: dict) -> dict:
    return {
        "current_step": manifest.get("current_step") or 1,
        "current_status": manifest.get("status") or "intent-captured",
        "current_owner_or_stage_actor": "human-sponsor",
        "blockers": [],
    }


def _load_optional_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_yaml(path)


def _step_binding(bindings: dict, step: int) -> dict:
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    return steps.get(step) or steps.get(str(step)) or steps.get(f"'{step}'") or {}


def _approval_for_step(human_gates: dict, step: int) -> dict:
    approvals = human_gates.get("approvals", {}) if isinstance(human_gates, dict) else {}
    if not isinstance(approvals, dict):
        return {}
    return approvals.get(step) or approvals.get(str(step)) or approvals.get(f"'{step}'") or {}


def _phase_index(step: int) -> int:
    if step <= 2:
        return 1
    if step <= 5:
        return 2
    if step <= 7:
        return 3
    return 4


def _status_for_step(step: int, matrix: dict) -> str:
    current_step = matrix.get("current_step")
    if isinstance(current_step, int):
        if step < current_step:
            return "completed"
        if step == current_step:
            return matrix.get("current_status") or "current"
    return "pending"


def _inputs_for_step(step: int, change_id: str) -> list[str]:
    defaults = {
        1: ["human goal", "source docs", "agent inventory"],
        2: [f".governance/changes/{change_id}/intent-confirmation.yaml", "scope assumptions"],
        3: ["confirmed intent", "constraints", "risks"],
        4: ["design direction", "requirements", "tasks"],
        5: ["contract.yaml", "bindings.yaml", "participants profile", "confirmed intent"],
        6: ["valid contract", "step 5 approval", "scope_in"],
        7: ["execution evidence", "verification commands"],
        8: ["verify result", "independent reviewer"],
        9: ["approved review", "continuity followups"],
    }
    return defaults[step]


def _outputs_for_step(step: int, change_id: str) -> list[str]:
    defaults = {
        1: [f".governance/changes/{change_id}/intent-confirmation.yaml"],
        2: [f".governance/changes/{change_id}/requirements.md"],
        3: [f".governance/changes/{change_id}/design.md"],
        4: [f".governance/changes/{change_id}/tasks.md", f".governance/changes/{change_id}/contract.yaml"],
        5: [f".governance/changes/{change_id}/bindings.yaml", f".governance/changes/{change_id}/step-reports/step-5.md"],
        6: [f".governance/changes/{change_id}/evidence/execution-summary.yaml"],
        7: [f".governance/changes/{change_id}/verify.yaml"],
        8: [f".governance/changes/{change_id}/review.yaml"],
        9: [f".governance/archive/{change_id}/archive-receipt.yaml"],
    }
    return defaults[step]


def _done_criteria(step: int, intent: dict) -> list[str]:
    if step in {1, 2, 5} and intent.get("status") != "confirmed":
        return ["intent confirmation is visible to the human", "open questions are reported before execution"]
    if step == 8:
        return ["review decision is explicit", "reviewer is independent from executor"]
    return ["owner has produced the expected outputs", "blockers and human decisions are reported"]


def _next_entry_criteria(step: int) -> list[str]:
    if step >= 9:
        return ["no next step; archive continuity is ready"]
    return [f"Step {step} report reviewed", f"Step {step + 1} owner is identified"]


def _human_decisions(step: int, binding: dict, intent: dict) -> list[str]:
    decisions = []
    if binding.get("human_gate"):
        decisions.append("Human gate is marked for this step.")
    if step <= 5 and intent.get("status") != "confirmed":
        decisions.append("Confirm project intent, scope, non-goals, and acceptance before Step 6.")
    if step == 8:
        decisions.append("Accept, revise, or reject the verified result.")
    return decisions or ["No human decision required by the current report."]


def _human_confirmation_options(binding: dict) -> list[dict]:
    if not binding.get("human_gate"):
        return []
    return [
        {"action": "approve", "label": "确认通过，进入下一步。"},
        {"action": "revise", "label": "需要修订，暂不进入下一步。"},
        {"action": "reject", "label": "拒绝通过，停止或重定向。"},
    ]


def _framework_controls(step: int, gate_type: str) -> list[str]:
    controls = [
        f"standard_step=Step {step}",
        f"gate_type={gate_type}",
        "Evidence and report facts must stay in the active change package.",
    ]
    if step == 5:
        controls.append("Step 6 must not start before Step 5 approval is recorded.")
    if step in {8, 9}:
        controls.append("Executor must not self-approve review or archive decisions.")
    return controls


def _agent_actions_done(step: int, change_dir: Path) -> list[str]:
    actions = [f"Generated Step {step} report from the active change package."]
    evidence = _evidence_summary(change_dir, step)
    for item in evidence:
        summary = item.get("summary")
        if summary:
            actions.append(str(summary))
    return actions


def _intent_summary(intent: dict, contract: dict) -> dict:
    if not intent and not contract:
        return {}
    source = "intent-confirmation" if intent else "contract"
    contract_scope_in = list(contract.get("scope_in", []))
    contract_scope_out = list(contract.get("scope_out", []))
    contract_acceptance = (contract.get("verification") or {}).get("checks", [])
    intent_scope_in = intent.get("scope_in", []) if intent else []
    intent_scope_out = intent.get("scope_out", []) if intent else []
    intent_acceptance = intent.get("acceptance_criteria", []) if intent else []
    scope_in = intent_scope_in or contract_scope_in
    scope_out = intent_scope_out or contract_scope_out
    acceptance = intent_acceptance or contract_acceptance
    merged_from = []
    if intent and contract:
        if not intent_scope_in and contract_scope_in:
            merged_from.append("contract.scope_in")
        if not intent_scope_out and contract_scope_out:
            merged_from.append("contract.scope_out")
        if not intent_acceptance and contract_acceptance:
            merged_from.append("contract.verification.checks")
    conflicts = []
    if intent and contract:
        if intent_scope_in and intent_scope_in != contract_scope_in:
            conflicts.append("intent scope_in differs from contract scope_in")
        if intent_scope_out and intent_scope_out != contract_scope_out:
            conflicts.append("intent scope_out differs from contract scope_out")
    return {
        "status": intent.get("status"),
        "facts_source": source,
        "merged_from": merged_from,
        "project_intent": intent.get("project_intent") or contract.get("objective"),
        "requirements": intent.get("requirements", []),
        "optimizations": intent.get("optimizations", []),
        "bugs": intent.get("bugs", []),
        "scope_in": scope_in,
        "scope_out": scope_out,
        "acceptance_criteria": acceptance,
        "risks": intent.get("risks", []),
        "open_questions": intent.get("open_questions", []),
        "fact_conflicts": conflicts,
    }


def _artifact_summary(change_dir: Path, step: int) -> dict:
    if step == 3:
        return {
            "design_summary": _first_non_heading_line(change_dir / "design.md"),
            **_contract_summary(change_dir),
        }
    if step == 4:
        return {
            "tasks": _markdown_bullets(change_dir / "tasks.md"),
            **_contract_summary(change_dir),
        }
    if step == 5:
        return _contract_summary(change_dir)
    if step == 8:
        lifecycle = _load_optional_yaml(change_dir / "review-lifecycle.yaml")
        review = _load_optional_yaml(change_dir / "review.yaml")
        invocation = _load_optional_yaml(change_dir / "review-invocation.yaml")
        baseline = _load_optional_yaml(change_dir / "baseline.yaml")
        summary = {
            "review_decision": (review.get("decision") or {}).get("status"),
            "review_lifecycle_status": lifecycle.get("status"),
            "review_rounds": len(lifecycle.get("rounds", [])) if lifecycle else 0,
        }
        if baseline:
            summary["baseline_dirty"] = baseline.get("dirty")
            summary["baseline_ref"] = "baseline.yaml"
        if lifecycle:
            latest_round = (lifecycle.get("rounds") or [])[-1] if lifecycle.get("rounds") else {}
            summary["latest_review_findings"] = latest_round.get("blocking_findings", [])
        if invocation:
            summary["review_invocation_status"] = invocation.get("status")
            summary["review_invocation_runtime"] = invocation.get("runtime")
            summary["review_invocation_last_heartbeat_at"] = invocation.get("last_heartbeat_at")
            summary["review_invocation_timeout_policy"] = invocation.get("timeout_policy")
        return summary
    if step == 7:
        verify = _load_optional_yaml(change_dir / "verify.yaml")
        product = verify.get("product_verification") or {}
        return {"product_verification_mode": product.get("mode"), "product_verification_commands": product.get("commands", [])} if product else {}
    if step == 9:
        review = _load_optional_yaml(change_dir / "review.yaml")
        verify = _load_optional_yaml(change_dir / "verify.yaml")
        receipt = _load_optional_yaml(change_dir / "archive-receipt.yaml")
        traceability = receipt.get("traceability") or {}
        review_followups = (review.get("conditions") or {}).get("followups", [])
        residual_followups = receipt.get("residual_followups", [])
        return {
            "archive_destination": str(change_dir).replace("/.governance/changes/", "/.governance/archive/"),
            "review_decision": (review.get("decision") or {}).get("status"),
            "verify_status": (verify.get("summary") or {}).get("status"),
            "archive_preview_files": list(traceability.values()) if traceability else _archive_preview_paths(change_dir),
            "carry_forward_items": [*review_followups, *residual_followups],
        }
    return {}


def _archive_preview_paths(change_dir: Path) -> list[str]:
    change_id = change_dir.name
    return [
        f".governance/archive/{change_id}/archive-receipt.yaml",
        f".governance/archive/{change_id}/manifest.yaml",
        f".governance/archive/{change_id}/review.yaml",
        f".governance/archive/{change_id}/verify.yaml",
        f".governance/archive/{change_id}/step-reports/step-9.yaml",
        f".governance/archive/{change_id}/FINAL_STATE_CONSISTENCY_CHECK.yaml",
        f".governance/archive/{change_id}/FINAL_STATUS_SNAPSHOT.yaml",
    ]


def _contract_summary(change_dir: Path) -> dict:
    contract = _load_optional_yaml(change_dir / "contract.yaml")
    return {
        "contract_scope_in": contract.get("scope_in", []),
        "contract_scope_out": contract.get("scope_out", []),
        "verification_commands": (contract.get("verification") or {}).get("commands", []),
    } if contract else {}


def _first_non_heading_line(path: Path) -> str:
    if not path.exists():
        return "missing"
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return "empty"


def _markdown_bullets(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip()[2:] for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("- ")]


def _review_gate_vs_decision(change_dir: Path, approval_state: str, gate_state: str) -> dict:
    review = _load_optional_yaml(change_dir / "review.yaml")
    return {
        "review_entry_gate": approval_state,
        "review_decision": (review.get("decision") or {}).get("status") or "none",
        "note": "review entry approval allows independent review to run; it is not the review decision",
    }


def _evidence_summary(change_dir: Path, step: int) -> list[dict]:
    evidence_dir = change_dir / "evidence"
    items: list[dict] = []
    if step == 6:
        execution = _load_optional_yaml(evidence_dir / "execution-summary.yaml")
        command = _load_optional_yaml(evidence_dir / "command-output-summary.yaml")
        tests = _load_optional_yaml(evidence_dir / "test-output-summary.yaml")
        changed = _load_optional_yaml(evidence_dir / "changed-files-manifest.yaml")
        if execution:
            items.append({
                "kind": "execution",
                "summary": f"execution run_id={execution.get('run_id')} status={execution.get('status')}",
                "run_id": execution.get("run_id"),
                "status": execution.get("status"),
                "artifacts": execution.get("artifacts", {}),
                "evidence_refs": execution.get("evidence_refs", []),
            })
        if command:
            items.append({"kind": "command_output", "summary": command.get("summary"), "command": command.get("command")})
        if tests:
            items.append({"kind": "test_output", "summary": tests.get("summary")})
        if changed:
            items.append({"kind": "changed_files", "created": changed.get("created", []), "modified": changed.get("modified", [])})
    if step == 7:
        verify = _load_optional_yaml(change_dir / "verify.yaml")
        if verify:
            items.append({
                "kind": "verify",
                "summary": f"verify_status: {verify.get('summary', {}).get('status')}",
                "verify_status": verify.get("summary", {}).get("status"),
                "blocker_count": verify.get("summary", {}).get("blocker_count"),
                "checks": verify.get("checks", []),
                "issues": verify.get("issues", []),
            })
    if step == 8:
        review = _load_optional_yaml(change_dir / "review.yaml")
        if review:
            items.append({
                "kind": "review",
                "summary": f"review_decision: {review.get('decision', {}).get('status')}",
                "review_decision": review.get("decision", {}).get("status"),
                "reviewers": review.get("reviewers", []),
                "conditions": review.get("conditions", {}),
                "runtime_evidence": review.get("runtime_evidence", {}),
            })
    return items


def _agent_actions_expected(step: int, binding: dict, status: str = "", approval_state: str = "") -> list[str]:
    if step == 9 and status == "archived":
        return ["Archive is complete; carry forward followups into the next active change."]
    if binding.get("human_gate") and approval_state == "approved" and step == 8:
        return ["Use the recorded review decision to choose Step 9 archive or revision work."]
    if binding.get("human_gate"):
        return ["Wait for a human approve / revise / reject action before advancing."]
    if step < 9:
        return [f"Prepare Step {step + 1} after current step outputs are complete."]
    return ["Carry forward archive followups into the next active change."]


def _recommended_next_action(step: int, binding: dict, intent: dict, status: str = "", approval_state: str = "") -> str:
    if step == 9 and status == "archived":
        return "Archive is complete; carry forward followups into the next change."
    if step <= 5 and intent.get("status") != "confirmed":
        return "Capture and confirm intent before allowing execution."
    if step == 8 and binding.get("human_gate") and approval_state == "approved":
        return "Continue based on the review decision: archive approved work or open a revision loop."
    if binding.get("human_gate"):
        return "Pause for human confirmation before advancing."
    if step < 9:
        return f"Prepare Step {step + 1} with the named owner."
    return "Archive is complete; carry forward followups into the next change."


def _format_report(payload: dict) -> str:
    lines = [
        f"# Step {payload['step']} Report: {payload['label']}",
        "",
        f"- change_id: {payload['change_id']}",
        f"- phase: {payload['phase']}",
        f"- standard_step: {payload['standard_step']}",
        f"- traditional_mapping: {payload['traditional_mapping']}",
        f"- status: {payload['status']}",
        f"- owner: {payload['owner']}",
        f"- assistants: {', '.join(payload['assistants']) or 'none'}",
        f"- reviewer: {payload.get('reviewer') or 'none'}",
        f"- human_gate: {str(payload['human_gate']).lower()}",
        f"- gate_type: {payload['gate_type']}",
        f"- gate_state: {payload['gate_state']}",
        f"- approval_state: {payload['approval_state']}",
        "",
        "## Participant responsibilities",
        *_bullets(payload["participant_responsibilities"]),
        "",
        "## Objective",
        payload["objective"],
        "",
        "## Inputs",
        *_bullets(payload["inputs"]),
        "",
        "## Outputs",
        *_bullets(payload["outputs"]),
        "",
        "## Intent summary",
        *_format_mapping(payload.get("intent_summary", {})),
        "",
        "## Artifact summary",
        *_format_mapping(payload.get("artifact_summary", {})),
        "",
        "## Review gate vs decision",
        *_format_mapping(payload.get("review_gate_vs_decision", {})),
        "",
        "## Evidence",
        *_format_evidence(payload.get("evidence", [])),
        "",
        "## Done criteria",
        *_bullets(payload["done_criteria"]),
        "",
        "## Next-entry criteria",
        *_bullets(payload["next_entry_criteria"]),
        "",
        "## Blockers",
        *_bullets(payload["blockers"] or ["none"]),
        "",
        "## Framework controls",
        *_bullets(payload["framework_controls"]),
        "",
        "## Agent actions done",
        *_bullets(payload["agent_actions_done"]),
        "",
        "## Agent actions expected",
        *_bullets(payload["agent_actions_expected"]),
        "",
        "## Human decisions required",
        *_bullets(payload["human_decisions_required"]),
        "",
        "## Human confirmation options",
        *_format_confirmation_options(payload["human_confirmation_options"]),
        "",
        "## Recommended next action",
        payload["recommended_next_action"],
    ]
    return "\n".join(lines) + "\n"


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _format_confirmation_options(items: list[dict]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item['action']}: {item['label']}" for item in items]


def _format_mapping(payload: dict) -> list[str]:
    if not payload:
        return ["- none"]
    lines = []
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"- {key}:")
            if value:
                for item in value:
                    lines.extend(_format_nested_value(item, indent="  - "))
            else:
                lines.append("  - none")
        elif isinstance(value, dict):
            lines.append(f"- {key}:")
            if value:
                for nested_key, nested_value in value.items():
                    lines.extend(_format_nested_value({nested_key: nested_value}, indent="  - "))
            else:
                lines.append("  - none")
        else:
            lines.append(f"- {key}: {value}")
    return lines


def _format_evidence(items: list[dict]) -> list[str]:
    if not items:
        return ["- none"]
    lines = []
    for item in items:
        lines.append(f"- {item.get('kind')}:")
        for key, value in item.items():
            if key == "kind":
                continue
            if isinstance(value, list):
                lines.append(f"  - {key}:")
                if value:
                    for entry in value:
                        lines.extend(_format_nested_value(entry, indent="    - "))
                else:
                    lines.append("    - none")
            elif isinstance(value, dict):
                lines.append(f"  - {key}:")
                if value:
                    for nested_key, nested_value in value.items():
                        lines.extend(_format_nested_value({nested_key: nested_value}, indent="    - "))
                else:
                    lines.append("    - none")
            else:
                lines.append(f"  - {key}: {value}")
    return lines


def _format_nested_value(value, *, indent: str) -> list[str]:
    if isinstance(value, dict):
        summary = ", ".join(f"{key}={nested}" for key, nested in value.items())
        return [f"{indent}{summary}"]
    return [f"{indent}{value}"]


def _participant_responsibilities(binding: dict) -> list[str]:
    owner = binding.get("owner") or "current owner"
    reviewer = binding.get("reviewer") or "reviewer"
    assistants = binding.get("assistants", [])
    responsibilities = [f"{owner}: produce the step outputs and report blockers before advancing."]
    if assistants:
        responsibilities.append(f"{', '.join(assistants)}: support the owner without taking final decision authority.")
    if reviewer:
        responsibilities.append(f"{reviewer}: check the step output against done criteria and gate expectations.")
    if binding.get("human_gate"):
        responsibilities.append("human gate owner: confirm the decision point before the next execution step proceeds.")
    return responsibilities


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
