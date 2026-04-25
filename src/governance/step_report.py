from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import ACTION_PURPOSES, PHASE_LABELS, STEP_LABELS, render_step_matrix


def materialize_step_report(root: str | Path, *, change_id: str, step: int | None = None) -> dict:
    package = read_change_package(root, change_id)
    matrix = render_step_matrix(root, change_id)
    selected_step = step or matrix["current_step"]
    if not isinstance(selected_step, int) or selected_step < 1 or selected_step > 9:
        raise ValueError("step must be an integer from 1 to 9")
    bindings = _load_optional_yaml(package.path / "bindings.yaml")
    intent = _load_optional_yaml(package.path / "intent-confirmation.yaml")
    step_binding = _step_binding(bindings, selected_step)
    payload = {
        "schema": "step-report/v1",
        "change_id": change_id,
        "step": selected_step,
        "phase": PHASE_LABELS[_phase_index(selected_step)],
        "label": STEP_LABELS[selected_step],
        "status": _status_for_step(selected_step, matrix),
        "owner": step_binding.get("owner") or matrix.get("current_owner_or_stage_actor"),
        "assistants": step_binding.get("assistants", []),
        "reviewer": step_binding.get("reviewer"),
        "human_gate": bool(step_binding.get("human_gate")),
        "participant_responsibilities": _participant_responsibilities(step_binding),
        "objective": ACTION_PURPOSES[selected_step],
        "inputs": _inputs_for_step(selected_step, change_id),
        "outputs": _outputs_for_step(selected_step, change_id),
        "done_criteria": _done_criteria(selected_step, intent),
        "next_entry_criteria": _next_entry_criteria(selected_step),
        "blockers": matrix.get("blockers", []),
        "human_decisions_required": _human_decisions(selected_step, step_binding, intent),
        "recommended_next_action": _recommended_next_action(selected_step, step_binding, intent),
        "generated_at": _now_utc(),
    }
    report_dir = package.path / "step-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(report_dir / f"step-{selected_step}.yaml", payload)
    (report_dir / f"step-{selected_step}.md").write_text(_format_report(payload), encoding="utf-8")
    return payload


def _load_optional_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_yaml(path)


def _step_binding(bindings: dict, step: int) -> dict:
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    return steps.get(step) or steps.get(str(step)) or steps.get(f"'{step}'") or {}


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


def _recommended_next_action(step: int, binding: dict, intent: dict) -> str:
    if step <= 5 and intent.get("status") != "confirmed":
        return "Capture and confirm intent before allowing execution."
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
        f"- status: {payload['status']}",
        f"- owner: {payload['owner']}",
        f"- assistants: {', '.join(payload['assistants']) or 'none'}",
        f"- reviewer: {payload.get('reviewer') or 'none'}",
        f"- human_gate: {str(payload['human_gate']).lower()}",
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
        "## Done criteria",
        *_bullets(payload["done_criteria"]),
        "",
        "## Next-entry criteria",
        *_bullets(payload["next_entry_criteria"]),
        "",
        "## Blockers",
        *_bullets(payload["blockers"] or ["none"]),
        "",
        "## Human decisions required",
        *_bullets(payload["human_decisions_required"]),
        "",
        "## Recommended next action",
        payload["recommended_next_action"],
    ]
    return "\n".join(lines) + "\n"


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


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
