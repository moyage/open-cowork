from __future__ import annotations

from pathlib import Path

from .change_package import read_change_package
from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml
from .step_matrix import render_status_snapshot


def intent_status(root: str | Path, change_id: str) -> dict:
    package = read_change_package(root, change_id)
    intent_path = package.path / "intent-confirmation.yaml"
    intent = load_yaml(intent_path) if intent_path.exists() else {}
    return {
        "schema": "intent-status/v1",
        "change_id": change_id,
        "status": intent.get("status", "missing"),
        "project_intent": intent.get("project_intent"),
        "requirements": intent.get("requirements", []),
        "scope_in": intent.get("scope_in", []),
        "scope_out": intent.get("scope_out", []),
        "acceptance_criteria": intent.get("acceptance_criteria", []),
        "risks": intent.get("risks", []),
        "open_questions": intent.get("open_questions", []),
        "ref": str(intent_path.relative_to(Path(root))) if intent_path.exists() else None,
    }


def participants_list(root: str | Path, change_id: str | None = None) -> dict:
    root_path = Path(root)
    profile_path = root_path / ".governance/participants.yaml"
    profile = load_yaml(profile_path) if profile_path.exists() else {}
    bindings = {}
    if change_id:
        package = read_change_package(root, change_id)
        bindings_path = package.path / "bindings.yaml"
        bindings = load_yaml(bindings_path) if bindings_path.exists() else {}
    binding_participants = bindings.get("participants") or []
    profile_participants = profile.get("participants") or []
    binding_steps = bindings.get("steps") or {}
    profile_matrix = profile.get("step_owner_matrix") or []
    return {
        "schema": "participants-list/v1",
        "change_id": change_id,
        "profile": profile.get("profile") or bindings.get("profile"),
        "participants": binding_participants or profile_participants,
        "step_owner_matrix": [] if binding_steps else profile_matrix,
        "bindings_steps": binding_steps,
        "refs": {
            "participants": str(profile_path.relative_to(root_path)) if profile_path.exists() else None,
            "bindings": f".governance/changes/{change_id}/bindings.yaml" if change_id else None,
        },
    }


def change_status(root: str | Path, change_id: str) -> dict:
    package = read_change_package(root, change_id)
    manifest = package.manifest
    try:
        snapshot = render_status_snapshot(root, change_id)
    except Exception:
        snapshot = {}
    return {
        "schema": "change-status/v1",
        "change_id": change_id,
        "title": manifest.get("title"),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
        "readiness": manifest.get("readiness", {}),
        "intent_confirmation": manifest.get("intent_confirmation", {}),
        "snapshot": snapshot,
        "ref": f".governance/changes/{change_id}/manifest.yaml",
    }


def last_archive_summary(root: str | Path) -> dict:
    paths = GovernancePaths(Path(root))
    maintenance = load_yaml(paths.maintenance_status_file()) if paths.maintenance_status_file().exists() else {}
    change_id = maintenance.get("last_archived_change")
    if not change_id:
        return {"schema": "last-archive-summary/v1", "status": "missing", "change_id": None}
    archive_dir = paths.archived_change_dir(str(change_id))
    receipt_path = archive_dir / "archive-receipt.yaml"
    review_path = archive_dir / "review.yaml"
    final_path = archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml"
    receipt = load_yaml(receipt_path) if receipt_path.exists() else {}
    review = load_yaml(review_path) if review_path.exists() else {}
    final = load_yaml(final_path) if final_path.exists() else {}
    traceability = receipt.get("traceability") or {}
    snapshot_ref = traceability.get("final_status_snapshot")
    if not snapshot_ref:
        snapshot_path = archive_dir / "FINAL_STATUS_SNAPSHOT.yaml"
        if snapshot_path.exists():
            snapshot_ref = str(snapshot_path.relative_to(paths.root))
    return {
        "schema": "last-archive-summary/v1",
        "status": "available",
        "change_id": str(change_id),
        "archived_at": maintenance.get("last_archive_at"),
        "archive_receipt": str(receipt_path.relative_to(paths.root)) if receipt_path.exists() else None,
        "archive_executed": receipt.get("archive_executed"),
        "review_decision": review.get("decision", {}).get("status"),
        "final_consistency": final.get("status"),
        "final_status_snapshot": snapshot_ref,
        "human_gate_summary": final.get("human_gate_summary", {}),
    }


def render_intent_status(payload: dict) -> str:
    lines = ["# Intent status", "", f"- change_id: {payload['change_id']}", f"- status: {payload['status']}", f"- project_intent: {payload.get('project_intent')}"]
    _extend_list(lines, "requirements", payload.get("requirements", []))
    _extend_list(lines, "scope_in", payload.get("scope_in", []))
    _extend_list(lines, "scope_out", payload.get("scope_out", []))
    _extend_list(lines, "acceptance_criteria", payload.get("acceptance_criteria", []))
    _extend_list(lines, "risks", payload.get("risks", []))
    _extend_list(lines, "open_questions", payload.get("open_questions", []))
    return "\n".join(lines) + "\n"


def render_participants_list(payload: dict) -> str:
    lines = ["# Participants", "", f"- change_id: {payload.get('change_id')}", f"- profile: {payload.get('profile')}", "", "## Participants"]
    for item in payload.get("participants", []):
        availability = item.get("availability")
        if availability:
            lines.append(f"- {item.get('id')} ({item.get('type')}, availability={availability}): {', '.join(item.get('strengths', []))}")
        else:
            lines.append(f"- {item.get('id')} ({item.get('type')}): {', '.join(item.get('strengths', []))}")
    if not payload.get("participants"):
        lines.append("- none")
    lines.extend(["", "## 9-step owner matrix"])
    matrix = payload.get("step_owner_matrix") or []
    if matrix:
        for item in matrix:
            lines.append(f"- Step {item.get('step')}: owner={item.get('primary_owner')} reviewer={item.get('reviewer')} human_gate={str(item.get('human_gate')).lower()}")
    else:
        for step, item in sorted((payload.get("bindings_steps") or {}).items(), key=lambda pair: int(str(pair[0]).strip("'"))):
            review_parts = []
            if item.get("reviewer"):
                review_parts.append(f"reviewer={item.get('reviewer')}")
            if item.get("runtime_reviewer"):
                review_parts.append(f"runtime_reviewer={item.get('runtime_reviewer')}")
            if item.get("fallback_reviewer"):
                review_parts.append(f"fallback_reviewer={item.get('fallback_reviewer')}")
            review_text = " ".join(review_parts)
            spacer = " " if review_text else ""
            lines.append(f"- Step {step}: owner={item.get('owner')}{spacer}{review_text} human_gate={str(item.get('human_gate')).lower()}")
    return "\n".join(lines) + "\n"


def render_change_status(payload: dict) -> str:
    lines = ["# Change status", "", f"- change_id: {payload['change_id']}", f"- title: {payload.get('title')}", f"- current_step: {payload.get('current_step')}", f"- current_status: {payload.get('status')}"]
    readiness = payload.get("readiness") or {}
    lines.append(f"- step6_entry_ready: {str(readiness.get('step6_entry_ready')).lower()}")
    intent = payload.get("intent_confirmation") or {}
    lines.append(f"- intent_status: {intent.get('status')}")
    return "\n".join(lines) + "\n"


def render_last_archive_summary(payload: dict) -> str:
    lines = ["# Last archived closeout", "", f"- change_id: {payload.get('change_id')}", f"- archived_at: {payload.get('archived_at')}", f"- archive_receipt: {payload.get('archive_receipt')}", f"- archive_executed: {payload.get('archive_executed')}", f"- review_decision: {payload.get('review_decision')}", f"- final_consistency: {payload.get('final_consistency')}", f"- final_status_snapshot: {payload.get('final_status_snapshot')}", "", "## Human gates"]
    gates = payload.get("human_gate_summary") or {}
    for step in (5, 8, 9):
        gate = gates.get(step) or gates.get(str(step)) or {}
        lines.append(f"- Step {step}: status={gate.get('status')} approved_by={gate.get('approved_by')}")
    return "\n".join(lines) + "\n"


def _extend_list(lines: list[str], label: str, items: list[str]) -> None:
    lines.extend(["", f"## {label}"])
    lines.extend([f"- {item}" for item in items] or ["- none"])
