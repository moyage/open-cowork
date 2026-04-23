from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package
from .index import read_changes_index, read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import PHASE_LABELS, STEP_LABELS, render_status_snapshot, render_step_matrix


def materialize_runtime_status(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    paths.runtime_status_dir.mkdir(parents=True, exist_ok=True)

    change_status = _build_change_status(paths, change_id)
    steps_status = _build_steps_status(paths, change_id)
    participants_status = _build_participants_status(paths, change_id, steps_status)

    write_yaml(paths.runtime_change_status_file(), change_status)
    write_yaml(paths.runtime_steps_status_file(), steps_status)
    write_yaml(paths.runtime_participants_status_file(), participants_status)
    return {
        "change_status_path": str(paths.runtime_change_status_file()),
        "steps_status_path": str(paths.runtime_steps_status_file()),
        "participants_status_path": str(paths.runtime_participants_status_file()),
        "change_status": change_status,
        "steps_status": steps_status,
        "participants_status": participants_status,
    }


def materialize_timeline(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    paths.runtime_timeline_dir.mkdir(parents=True, exist_ok=True)
    payload = _build_timeline_payload(paths, change_id)
    target = paths.runtime_timeline_month_file(payload["month"])
    write_yaml(target, payload)
    return {"path": str(target), "payload": payload}


def _build_change_status(paths: GovernancePaths, change_id: str) -> dict:
    snapshot = render_status_snapshot(paths.root, change_id)
    matrix = render_step_matrix(paths.root, change_id)
    current = read_current_change(paths.root)
    maintenance = load_yaml(paths.maintenance_status_file())
    current_step = matrix["current_step"]
    completed_steps = _completed_steps(current_step, matrix["current_status"])
    remaining_steps = [step for step in range(1, 10) if step not in completed_steps]
    return {
        "schema": "runtime-change-status/v1",
        "change_id": change_id,
        "phase": snapshot["current_phase"],
        "current_step": current_step,
        "current_status": matrix["current_status"],
        "overall_progress": {
            "completed_steps": completed_steps,
            "remaining_steps": remaining_steps,
        },
        "gate_posture": {
            "waiting_on": snapshot["waiting_on"],
            "next_decision": snapshot["next_decision"],
            "human_intervention_required": snapshot["human_intervention_required"],
        },
        "current_owner": snapshot["current_owner"],
        "maintenance_status": maintenance.get("status"),
        "refs": {
            "manifest": str(paths.change_file(change_id, "manifest.yaml").relative_to(paths.root)),
            "current_change": str(paths.current_change_file().relative_to(paths.root)),
            "changes_index": str(paths.changes_index_file().relative_to(paths.root)),
            "maintenance_status": str(paths.maintenance_status_file().relative_to(paths.root)),
        },
        "generated_at": _now_utc(),
        "active_change_matches_current": (current.get("current_change_id") == change_id),
    }


def _build_steps_status(paths: GovernancePaths, change_id: str) -> dict:
    matrix = render_step_matrix(paths.root, change_id)
    package = read_change_package(paths.root, change_id)
    bindings = _load_optional_yaml(paths.change_file(change_id, "bindings.yaml"))
    current_step = matrix["current_step"]
    current_status = str(matrix["current_status"])
    steps = []
    for step in range(1, 10):
        binding = _step_binding(bindings, step)
        steps.append({
            "step": step,
            "label": STEP_LABELS[step],
            "owner": binding.get("owner") or _role_owner_for_step(package.manifest, step),
            "status": _step_status(step, current_step, current_status),
            "gate": binding.get("gate") or _default_gate(step),
            "human_intervention_required": _gate_requires_human(binding.get("gate") or _default_gate(step)),
        })
    return {
        "schema": "runtime-steps-status/v1",
        "change_id": change_id,
        "phase": PHASE_LABELS[_phase_index(current_step)],
        "current_step": current_step,
        "steps": steps,
        "generated_at": _now_utc(),
    }


def _build_participants_status(paths: GovernancePaths, change_id: str, steps_status: dict) -> dict:
    package = read_change_package(paths.root, change_id)
    bindings = _load_optional_yaml(paths.change_file(change_id, "bindings.yaml"))
    roles = package.manifest.get("roles", {})
    participants = []
    for role, step in (("executor", 6), ("verifier", 7), ("reviewer", 8)):
        actor_id = roles.get(role) or _step_binding(bindings, step).get("owner")
        if not actor_id:
            continue
        step_payload = next((item for item in steps_status["steps"] if item["step"] == step), {})
        participants.append({
            "actor_id": actor_id,
            "actor_type": "agent",
            "role": role,
            "step": step,
            "status": _participant_status(step_payload.get("status")),
        })
    return {
        "schema": "runtime-participants-status/v1",
        "change_id": change_id,
        "participants": participants,
        "generated_at": _now_utc(),
    }


def _build_timeline_payload(paths: GovernancePaths, change_id: str) -> dict:
    package = read_change_package(paths.root, change_id)
    manifest = package.manifest
    verify = _load_optional_yaml(paths.change_file(change_id, "verify.yaml"))
    review = _load_optional_yaml(paths.change_file(change_id, "review.yaml"))
    archive_receipt = _load_optional_yaml(paths.archived_change_file(change_id, "archive-receipt.yaml"))
    changes_index = read_changes_index(paths.root)
    entry = next((item for item in changes_index.get("changes", []) if item.get("change_id") == change_id), {})
    month = datetime.utcnow().strftime("%Y%m")
    events = []
    events.append(_event(change_id, "change_created", 5, "drafting", entry.get("status") or manifest.get("status"), "orchestrator", [
        str(paths.change_dir(change_id).relative_to(paths.root)) + "/",
    ]))
    if verify:
        events.append(_event(change_id, "verify_completed", 7, "step6-executed-pre-step7", verify.get("summary", {}).get("status") == "pass" and "step7-verified" or "step7-blocked", _actor_for_verify(manifest), [
            str(paths.change_file(change_id, "verify.yaml").relative_to(paths.root)),
        ]))
    if review:
        events.append(_event(change_id, "review_completed", 8, "step7-verified", _status_for_review(review), _actor_for_review(manifest, review), [
            str(paths.change_file(change_id, "review.yaml").relative_to(paths.root)),
        ]))
    if archive_receipt:
        events.append(_event(change_id, "archive_completed", 9, "review-approved", "archived", _actor_for_review(manifest, review), [
            str(paths.archived_change_file(change_id, "archive-receipt.yaml").relative_to(paths.root)),
        ]))
    return {
        "schema": "runtime-timeline/v1",
        "change_id": change_id,
        "month": month,
        "events": events,
        "generated_at": _now_utc(),
    }


def _event(
    change_id: str,
    event_type: str,
    step: int,
    from_status: str | None,
    to_status: str | None,
    actor_id: str | None,
    refs: list[str],
) -> dict:
    return {
        "schema": "runtime-event/v1",
        "event_id": f"{change_id}-{event_type}",
        "change_id": change_id,
        "entity_type": "change",
        "event_type": event_type,
        "step": step,
        "from_status": from_status,
        "to_status": to_status,
        "actor_id": actor_id or "governance",
        "timestamp": _now_utc(),
        "refs": {"files": refs},
    }


def _completed_steps(current_step: int | str, current_status: str | None) -> list[int]:
    if not isinstance(current_step, int):
        return []
    completed = [step for step in range(1, current_step) if step <= 9]
    status_text = str(current_status)
    if current_status and (
        status_text.startswith("step6-executed")
        or status_text.startswith("step7-")
        or status_text.startswith("review-")
        or status_text == "archived"
    ):
        if current_step not in completed:
            completed.append(current_step)
    return completed


def _step_status(step: int, current_step: int | str, current_status: str) -> str:
    if not isinstance(current_step, int):
        return "pending"
    completed_steps = _completed_steps(current_step, current_status)
    if step in completed_steps:
        return "completed"
    if step == current_step + 1 and current_status not in {"archived"}:
        return "waiting_gate"
    if step == current_step:
        if "blocked" in current_status or "rejected" in current_status:
            return "blocked"
        return "in_progress"
    return "pending"


def _participant_status(step_status: str | None) -> str:
    if step_status == "completed":
        return "completed"
    if step_status == "waiting_gate":
        return "waiting_input"
    if step_status == "blocked":
        return "blocked"
    return "standby"


def _actor_for_verify(manifest: dict) -> str | None:
    return manifest.get("roles", {}).get("verifier") or manifest.get("roles", {}).get("reviewer")


def _actor_for_review(manifest: dict, review: dict) -> str | None:
    reviewers = review.get("reviewers", []) if isinstance(review, dict) else []
    if reviewers:
        return reviewers[0].get("id")
    return manifest.get("roles", {}).get("reviewer")


def _status_for_review(review: dict) -> str:
    decision = review.get("decision", {}).get("status")
    if decision == "approve":
        return "review-approved"
    if decision == "reject":
        return "review-rejected"
    if decision == "revise":
        return "review-revise"
    return "review-pending"


def _role_owner_for_step(manifest: dict, step: int) -> str:
    roles = manifest.get("roles", {})
    if step == 6:
        return roles.get("executor") or "executor"
    if step == 7:
        return roles.get("verifier") or roles.get("reviewer") or "verifier"
    if step == 8:
        return roles.get("reviewer") or "reviewer"
    if step == 9:
        return roles.get("reviewer") or roles.get("formal_orchestrator") or "governance"
    return roles.get("formal_orchestrator") or roles.get("owner") or "governance"


def _default_gate(step: int) -> str:
    if step in {5, 8, 9}:
        return "approval-required"
    if step in {1, 3, 7}:
        return "review-required"
    if step == 6:
        return "auto-pass"
    return "guided"


def _gate_requires_human(gate: str) -> bool:
    return gate in {"approval-required", "review-required"}


def _step_binding(bindings: dict, step: int) -> dict:
    steps = bindings.get("steps", {})
    return steps.get(str(step)) or steps.get(step) or {}


def _phase_index(current_step: int | str) -> int:
    if not isinstance(current_step, int):
        return 1
    if current_step <= 2:
        return 1
    if current_step <= 5:
        return 2
    if current_step <= 7:
        return 3
    return 4


def _load_optional_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_yaml(path)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
