from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .index import read_changes_index, read_current_change
from .paths import GovernancePaths
from .runtime_status import materialize_runtime_status
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import render_status_snapshot

CONTINUITY_LAUNCH_INPUT_SCHEMA = "continuity-launch-input/v1"
ROUND_ENTRY_INPUT_SUMMARY_SCHEMA = "round-entry-input-summary/v1"
HANDOFF_PACKAGE_SCHEMA = "handoff-package/v1"
OWNER_TRANSFER_CONTINUITY_SCHEMA = "owner-transfer-continuity/v1"
INCREMENT_PACKAGE_SCHEMA = "increment-package/v1"


def resolve_continuity_launch_input(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    current_change = read_current_change(root)
    resolved_change_id = change_id or _extract_current_change_id(current_change)
    if not resolved_change_id:
        raise ValueError("no change_id provided and no current change set")

    changes_index = read_changes_index(root)
    current_entry = _find_change_entry(changes_index, str(resolved_change_id))
    current_manifest = _load_change_manifest(paths, str(resolved_change_id))
    predecessor_change = current_entry.get("predecessor_change") or current_manifest.get("predecessor_change")
    if not predecessor_change:
        raise ValueError(f"change '{resolved_change_id}' does not declare predecessor_change")

    maintenance_status = load_yaml(paths.maintenance_status_file())
    archive_map = load_yaml(paths.archive_map_file())
    archive_entry = _find_archive_entry(archive_map, predecessor_change)
    maintenance_last_archived_change = maintenance_status.get("last_archived_change")
    if _extract_current_change_id(current_change) != str(resolved_change_id) and maintenance_last_archived_change != predecessor_change:
        maintenance_last_archived_change = predecessor_change

    if _extract_current_change_id(current_change) == str(resolved_change_id) and maintenance_status.get("last_archived_change") != predecessor_change:
        raise ValueError(
            "predecessor_change does not match maintenance baseline last_archived_change"
        )

    predecessor_manifest_path = paths.archived_change_file(predecessor_change, "manifest.yaml")
    predecessor_review_path = paths.archived_change_file(predecessor_change, "review.yaml")
    archive_receipt_path = paths.root / str(archive_entry.get("receipt", ""))
    predecessor_manifest = load_yaml(predecessor_manifest_path)
    predecessor_review = load_yaml(predecessor_review_path)
    archive_receipt = load_yaml(archive_receipt_path)

    if not archive_receipt.get("archive_executed"):
        raise ValueError(f"predecessor archive receipt for '{predecessor_change}' is not executed")

    review_decision = predecessor_review.get("decision", {}).get("status")
    if not review_decision:
        raise ValueError(f"predecessor review for '{predecessor_change}' is missing decision status")

    current_step = current_entry.get("current_step") or current_manifest.get("current_step")
    decision_summary = {
        "current_phase": _phase_label_for_step(current_step),
        "current_summary": {
            "change_id": str(resolved_change_id),
            "status": current_entry.get("status") or current_manifest.get("status"),
            "validation_focus": current_entry.get("validation_focus") or current_manifest.get("validation_focus"),
            "predecessor_change": predecessor_change,
        },
        "current_blockers": [],
        "next_decision": _decision_point_for_step(current_step),
        "next_input_suggestion": [
            str(paths.change_file(str(resolved_change_id), "manifest.yaml").relative_to(paths.root)),
            str(paths.change_file(str(resolved_change_id), "contract.yaml").relative_to(paths.root)),
            str(paths.change_file(str(resolved_change_id), "bindings.yaml").relative_to(paths.root)),
        ],
    }

    return {
        "schema": CONTINUITY_LAUNCH_INPUT_SCHEMA,
        "change_id": str(resolved_change_id),
        "continuity_mode": "previous_round_review_archive_maintenance_to_launch_input",
        "baseline_inputs_used": [
            ".governance/index/current-change.yaml",
            ".governance/index/changes-index.yaml",
            ".governance/index/maintenance-status.yaml",
            ".governance/index/archive-map.yaml",
            str(predecessor_review_path.relative_to(paths.root)),
            str(predecessor_manifest_path.relative_to(paths.root)),
            str(archive_receipt_path.relative_to(paths.root)),
        ],
        "current_change": {
            "change_id": current_entry.get("change_id") or current_entry.get("id") or str(resolved_change_id),
            "path": current_entry.get("path") or str(paths.change_dir(str(resolved_change_id)).relative_to(paths.root)),
            "status": current_entry.get("status") or current_manifest.get("status"),
            "current_step": current_entry.get("current_step") or current_manifest.get("current_step"),
            "validation_focus": current_entry.get("validation_focus") or current_manifest.get("validation_focus"),
            "predecessor_change": predecessor_change,
        },
        "predecessor_review_baseline": {
            "change_id": predecessor_change,
            "path": str(predecessor_review_path.relative_to(paths.root)),
            "decision_status": review_decision,
            "step9_entry_ready": predecessor_review.get("pre_step9_condition_closure", {}).get("step9_entry_ready"),
            "not_step9_archive_statement": predecessor_review.get("statement", {}).get("not_step9_archive"),
        },
        "predecessor_archive_baseline": {
            "change_id": predecessor_change,
            "path": str(predecessor_manifest_path.relative_to(paths.root)),
            "archive_path": archive_entry.get("archive_path"),
            "archive_receipt": str(archive_receipt_path.relative_to(paths.root)),
            "archived_at": archive_receipt.get("archived_at") or archive_entry.get("archived_at"),
            "archive_executed": archive_receipt.get("archive_executed"),
            "lifecycle_step9_status": predecessor_manifest.get("lifecycle", {}).get("step9", {}).get("status"),
        },
        "maintenance_baseline": {
            "path": ".governance/index/maintenance-status.yaml",
            "status": maintenance_status.get("status"),
            "current_change_active": maintenance_status.get("current_change_active"),
            "current_change_id": maintenance_status.get("current_change_id"),
            "last_archived_change": maintenance_last_archived_change,
        },
        "launch_readiness": {
            "baseline_consistent": True,
            "archived_predecessor_available": True,
            "review_to_archive_to_launch_chain_explicit": True,
        },
        "decision_summary": decision_summary,
        "not_step7_8_9": {
            "step7_verify": False,
            "step8_review": False,
            "step9_archive": False,
        },
    }


def materialize_continuity_launch_input(root: str | Path, change_id: str | None = None) -> str:
    payload = resolve_continuity_launch_input(root, change_id)
    target = GovernancePaths(Path(root)).continuity_launch_input_file(payload["change_id"])
    write_yaml(target, payload)
    return str(target)


def resolve_round_entry_input_summary(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    continuity_payload = resolve_continuity_launch_input(root, change_id)
    resolved_change_id = continuity_payload["change_id"]

    operator_start_pack = [
        _path_ref(paths, resolved_change_id, "manifest.yaml"),
        _path_ref(paths, resolved_change_id, "contract.yaml"),
        _path_ref(paths, resolved_change_id, "requirements.md"),
        _path_ref(paths, resolved_change_id, "tasks.md"),
        _path_ref(paths, resolved_change_id, "bindings.yaml"),
        {"path": ".governance/index/current-change.yaml", "role": "active-pointer"},
    ]
    supporting_authoritative = [
        _path_ref(paths, resolved_change_id, "intent.md"),
        _path_ref(paths, resolved_change_id, "design.md"),
        {"path": ".governance/index/changes-index.yaml", "role": "history-pointer"},
        {"path": ".governance/index/maintenance-status.yaml", "role": "maintenance-posture"},
    ]
    carry_forward_baseline = [
        {
            "path": continuity_payload["predecessor_review_baseline"]["path"],
            "role": "predecessor-review-baseline",
        },
        {
            "path": continuity_payload["predecessor_archive_baseline"]["path"],
            "role": "predecessor-archive-manifest",
        },
        {
            "path": continuity_payload["predecessor_archive_baseline"]["archive_receipt"],
            "role": "predecessor-archive-receipt",
        },
    ]

    return {
        "schema": ROUND_ENTRY_INPUT_SUMMARY_SCHEMA,
        "change_id": resolved_change_id,
        "purpose": "smaller-round-entry-reading-surface",
        "operator_start_pack": operator_start_pack,
        "supporting_authoritative": supporting_authoritative,
        "carry_forward_baseline": carry_forward_baseline,
        "usage_rule": {
            "read_first": [item["path"] for item in operator_start_pack],
            "read_if_needed": [item["path"] for item in supporting_authoritative],
            "carry_forward_reference": [item["path"] for item in carry_forward_baseline],
        },
    }


def materialize_round_entry_input_summary(root: str | Path, change_id: str | None = None) -> str:
    payload = resolve_round_entry_input_summary(root, change_id)
    target = GovernancePaths(Path(root)).round_entry_input_summary_file(payload["change_id"])
    write_yaml(target, payload)
    return str(target)


def resolve_handoff_package(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    current_change = read_current_change(root)
    resolved_change_id = change_id or _extract_current_change_id(current_change)
    if not resolved_change_id:
        raise ValueError("no change_id provided and no current change set")

    current_entry = _find_change_entry(read_changes_index(root), str(resolved_change_id))
    manifest = _load_change_manifest(paths, str(resolved_change_id))
    if not manifest:
        raise ValueError(f"change '{resolved_change_id}' is missing manifest.yaml")

    runtime_payload = _ensure_runtime_status_payload(paths, str(resolved_change_id))
    snapshot = render_status_snapshot(root, str(resolved_change_id))
    contract = _load_optional_yaml(paths.change_file(str(resolved_change_id), "contract.yaml"))
    bindings = _load_optional_yaml(paths.change_file(str(resolved_change_id), "bindings.yaml"))
    roles = manifest.get("roles", {})

    payload = {
        "schema": HANDOFF_PACKAGE_SCHEMA,
        "change_id": str(resolved_change_id),
        "handoff_kind": "active-change",
        "generated_at": _now_utc(),
        "summary": {
            "project_summary": snapshot.get("project_summary"),
            "current_phase": runtime_payload["change_status"].get("phase"),
            "current_step": runtime_payload["change_status"].get("current_step"),
            "current_status": runtime_payload["change_status"].get("current_status"),
            "current_owner": runtime_payload["change_status"].get("current_owner"),
            "waiting_on": runtime_payload["change_status"].get("gate_posture", {}).get("waiting_on"),
            "next_decision": runtime_payload["change_status"].get("gate_posture", {}).get("next_decision"),
        },
        "handoff_need": {
            "handoff_reason": "session-handoff",
            "intended_receiver_type": "agent",
            "intended_receiver_role": _intended_receiver_role(runtime_payload["steps_status"]),
            "human_intervention_required": runtime_payload["change_status"].get("gate_posture", {}).get("human_intervention_required"),
        },
        "execution_context": {
            "target_validation_objects": list(contract.get("validation_objects", [])) or list(manifest.get("target_validation_objects", [])),
            "active_roles": {
                "executor": roles.get("executor") or _step_binding(bindings, 6).get("owner"),
                "verifier": roles.get("verifier") or _step_binding(bindings, 7).get("owner"),
                "reviewer": roles.get("reviewer") or _step_binding(bindings, 8).get("owner"),
            },
            "current_gate": _current_gate(runtime_payload["steps_status"]),
        },
        "operator_start_pack": _operator_start_pack(paths, str(resolved_change_id)),
        "refs": _handoff_refs(paths, str(resolved_change_id)),
    }
    carry_forward = _carry_forward_section(paths, str(resolved_change_id), current_entry, manifest)
    if carry_forward:
        payload["carry_forward"] = carry_forward
    return payload


def materialize_handoff_package(root: str | Path, change_id: str | None = None) -> str:
    payload = resolve_handoff_package(root, change_id)
    target = GovernancePaths(Path(root)).handoff_package_file(payload["change_id"])
    write_yaml(target, payload)
    return str(target)


def prepare_owner_transfer_continuity(
    root: str | Path,
    *,
    change_id: str,
    target_role: str,
    outgoing_owner: str,
    incoming_owner: str,
    reason: str,
    initiated_by: str,
) -> str:
    paths = GovernancePaths(Path(root))
    handoff_path = paths.handoff_package_file(change_id)
    if not handoff_path.exists():
        materialize_handoff_package(root, change_id)
    handoff_payload = load_yaml(handoff_path)
    runtime_payload = _ensure_runtime_status_payload(paths, change_id)
    payload = {
        "schema": OWNER_TRANSFER_CONTINUITY_SCHEMA,
        "change_id": change_id,
        "generated_at": _now_utc(),
        "transfer_context": {
            "transfer_reason": reason,
            "target_role": target_role,
            "outgoing_owner": outgoing_owner,
            "incoming_owner": incoming_owner,
            "initiated_by": initiated_by,
        },
        "state_snapshot": {
            "current_status": handoff_payload.get("summary", {}).get("current_status"),
            "current_step": handoff_payload.get("summary", {}).get("current_step"),
            "current_phase": handoff_payload.get("summary", {}).get("current_phase"),
            "human_intervention_required": handoff_payload.get("handoff_need", {}).get("human_intervention_required"),
        },
        "acceptance": {
            "status": "pending",
            "accepted_by": None,
            "accepted_at": None,
            "note": "",
        },
        "effects": {
            "current_change_pointer_update_required": False,
            "bindings_update_required": True,
            "contract_update_required": False,
        },
        "refs": {
            "handoff_package": str(handoff_path.relative_to(paths.root)),
            "runtime_change_status": str(paths.runtime_change_status_file().relative_to(paths.root)),
            "runtime_participants_status": str(paths.runtime_participants_status_file().relative_to(paths.root)),
            "current_change": str(paths.current_change_file().relative_to(paths.root)),
            "bindings": str(paths.change_file(change_id, "bindings.yaml").relative_to(paths.root)),
        },
    }
    target = paths.owner_transfer_continuity_file(change_id)
    write_yaml(target, payload)
    return str(target)


def accept_owner_transfer_continuity(
    root: str | Path,
    *,
    change_id: str,
    accepted_by: str,
    note: str = "",
) -> dict:
    paths = GovernancePaths(Path(root))
    target = paths.owner_transfer_continuity_file(change_id)
    if not target.exists():
        raise ValueError(f"owner transfer continuity for '{change_id}' does not exist")
    payload = load_yaml(target)
    acceptance = payload.setdefault("acceptance", {})
    if acceptance.get("status") != "pending":
        raise ValueError("owner transfer continuity is not pending")
    acceptance.update({
        "status": "accepted",
        "accepted_by": accepted_by,
        "accepted_at": _now_utc(),
        "note": note,
    })
    write_yaml(target, payload)
    return payload


def resolve_increment_package(
    root: str | Path,
    *,
    change_id: str,
    reason: str,
    segment_owner: str,
    segment_label: str,
    new_findings: list[str],
    invalidated_assumptions: list[str],
    new_risks: list[str],
    blockers: list[str],
    next_followups: list[str],
) -> dict:
    if not any([new_findings, invalidated_assumptions, new_risks, blockers, next_followups]):
        raise ValueError("increment package requires at least one delta item")
    paths = GovernancePaths(Path(root))
    handoff_path = paths.handoff_package_file(change_id)
    if not handoff_path.exists():
        materialize_handoff_package(root, change_id)
    handoff_payload = load_yaml(handoff_path)
    runtime_payload = _ensure_runtime_status_payload(paths, change_id)
    refs = {
        "handoff_package": str(handoff_path.relative_to(paths.root)),
        "runtime_change_status": str(paths.runtime_change_status_file().relative_to(paths.root)),
        "runtime_timeline": str(paths.runtime_timeline_month_file().relative_to(paths.root)),
    }
    verify_path = paths.change_file(change_id, "verify.yaml")
    if verify_path.exists():
        refs["verify"] = str(verify_path.relative_to(paths.root))
    owner_transfer_path = paths.owner_transfer_continuity_file(change_id)
    if owner_transfer_path.exists():
        refs["owner_transfer"] = str(owner_transfer_path.relative_to(paths.root))
    return {
        "schema": INCREMENT_PACKAGE_SCHEMA,
        "change_id": change_id,
        "generated_at": _now_utc(),
        "increment_context": {
            "increment_reason": reason,
            "segment_owner": segment_owner,
            "segment_label": segment_label,
        },
        "state_anchor": {
            "current_status": handoff_payload.get("summary", {}).get("current_status"),
            "current_step": handoff_payload.get("summary", {}).get("current_step"),
            "current_phase": handoff_payload.get("summary", {}).get("current_phase"),
            "next_decision": handoff_payload.get("summary", {}).get("next_decision")
            or runtime_payload["change_status"].get("gate_posture", {}).get("next_decision"),
        },
        "delta": {
            "new_findings": list(new_findings),
            "invalidated_assumptions": list(invalidated_assumptions),
            "new_risks": list(new_risks),
            "blockers": list(blockers),
            "next_followups": list(next_followups),
        },
        "refs": refs,
    }


def materialize_increment_package(
    root: str | Path,
    *,
    change_id: str,
    reason: str,
    segment_owner: str,
    segment_label: str,
    new_findings: list[str],
    invalidated_assumptions: list[str],
    new_risks: list[str],
    blockers: list[str],
    next_followups: list[str],
) -> str:
    payload = resolve_increment_package(
        root,
        change_id=change_id,
        reason=reason,
        segment_owner=segment_owner,
        segment_label=segment_label,
        new_findings=new_findings,
        invalidated_assumptions=invalidated_assumptions,
        new_risks=new_risks,
        blockers=blockers,
        next_followups=next_followups,
    )
    target = GovernancePaths(Path(root)).increment_package_file(change_id)
    write_yaml(target, payload)
    return str(target)


def _path_ref(paths: GovernancePaths, change_id: str, name: str) -> dict:
    return {
        "path": str(paths.change_file(change_id, name).relative_to(paths.root)),
        "role": name,
    }


def _find_change_entry(changes_index: dict, change_id: str) -> dict:
    for entry in changes_index.get("changes", []):
        if entry.get("change_id") == change_id or entry.get("id") == change_id:
            return entry
    raise ValueError(f"change '{change_id}' not found in changes index")


def _ensure_runtime_status_payload(paths: GovernancePaths, change_id: str) -> dict:
    if not paths.runtime_change_status_file().exists():
        return materialize_runtime_status(paths.root, change_id)
    payload = {
        "change_status": load_yaml(paths.runtime_change_status_file()),
        "steps_status": load_yaml(paths.runtime_steps_status_file()),
        "participants_status": load_yaml(paths.runtime_participants_status_file()),
    }
    if payload["change_status"].get("change_id") != change_id:
        return materialize_runtime_status(paths.root, change_id)
    return payload


def _extract_current_change_id(payload: dict) -> str | None:
    nested = payload.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    return payload.get("current_change_id") or nested.get("change_id") or nested.get("current_change_id")


def _load_change_manifest(paths: GovernancePaths, change_id: str) -> dict:
    draft_manifest = paths.change_file(change_id, "manifest.yaml")
    if draft_manifest.exists():
        return load_yaml(draft_manifest)
    archived_manifest = paths.archived_change_file(change_id, "manifest.yaml")
    if archived_manifest.exists():
        return load_yaml(archived_manifest)
    return {}


def _load_optional_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return load_yaml(path)


def _handoff_refs(paths: GovernancePaths, change_id: str) -> dict:
    refs = {
        "runtime_change_status": str(paths.runtime_change_status_file().relative_to(paths.root)),
        "runtime_steps_status": str(paths.runtime_steps_status_file().relative_to(paths.root)),
        "runtime_participants_status": str(paths.runtime_participants_status_file().relative_to(paths.root)),
    }
    verify_path = paths.change_file(change_id, "verify.yaml")
    review_path = paths.change_file(change_id, "review.yaml")
    if verify_path.exists():
        refs["verify"] = str(verify_path.relative_to(paths.root))
    if review_path.exists():
        refs["review"] = str(review_path.relative_to(paths.root))
    return refs


def _carry_forward_section(paths: GovernancePaths, change_id: str, current_entry: dict, manifest: dict) -> dict | None:
    predecessor_change = current_entry.get("predecessor_change") or manifest.get("predecessor_change")
    launch_input = paths.continuity_launch_input_file(change_id)
    round_entry = paths.round_entry_input_summary_file(change_id)
    refs = []
    if launch_input.exists():
        refs.append(str(launch_input.relative_to(paths.root)))
    if round_entry.exists():
        refs.append(str(round_entry.relative_to(paths.root)))
    if not refs:
        return None
    payload = {"carry_forward_refs": refs}
    if predecessor_change:
        payload["predecessor_change"] = predecessor_change
    return payload


def _operator_start_pack(paths: GovernancePaths, change_id: str) -> list[str]:
    names = ["manifest.yaml", "contract.yaml", "tasks.md", "bindings.yaml"]
    refs = []
    for name in names:
        path = paths.change_file(change_id, name)
        if path.exists():
            refs.append(str(path.relative_to(paths.root)))
    return refs


def _intended_receiver_role(steps_status: dict) -> str | None:
    next_step = steps_status.get("next_step")
    step_payload = next((item for item in steps_status.get("steps", []) if item.get("step") == next_step), None)
    if not step_payload:
        return None
    if next_step == 7:
        return "verifier"
    if next_step == 8:
        return "reviewer"
    if next_step == 9:
        return "archiver"
    return step_payload.get("owner")


def _current_gate(steps_status: dict) -> str | None:
    next_step = steps_status.get("next_step")
    step_payload = next((item for item in steps_status.get("steps", []) if item.get("step") == next_step), None)
    if step_payload:
        return step_payload.get("gate")
    current_step = steps_status.get("current_step")
    current_payload = next((item for item in steps_status.get("steps", []) if item.get("step") == current_step), None)
    return current_payload.get("gate") if current_payload else None


def _step_binding(bindings: dict, step: int) -> dict:
    steps = bindings.get("steps", {})
    if not isinstance(steps, dict):
        return {}
    return steps.get(str(step), {}) or steps.get(step, {}) or {}


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _find_archive_entry(archive_map: dict, change_id: str) -> dict:
    for entry in archive_map.get("archives", []):
        if entry.get("change_id") == change_id:
            return entry
    raise ValueError(f"archived change '{change_id}' not found in archive map")


def _phase_label_for_step(step) -> str:
    if isinstance(step, str) and step.isdigit():
        step = int(step)
    if not isinstance(step, int):
        return "Phase 1 / 定义与对齐"
    if step <= 2:
        return "Phase 1 / 定义与对齐"
    if step <= 5:
        return "Phase 2 / 方案与准备"
    if step <= 7:
        return "Phase 3 / 执行与验证"
    return "Phase 4 / 审查与收束"


def _decision_point_for_step(step) -> str:
    if isinstance(step, str) and step.isdigit():
        step = int(step)
    if not isinstance(step, int):
        return "Step 1 / Clarify the goal"
    if step in {1, 2, 3, 5, 8, 9}:
        return f"Step {step} / {_step_label(step)}"
    if step < 5:
        return f"Step {step + 1} / {_step_label(step + 1)}"
    if step in {6, 7}:
        return "Step 8 / Review and decide"
    return "none"


def _step_label(step: int) -> str:
    labels = {
        1: "Clarify the goal",
        2: "Lock the scope",
        3: "Shape the approach",
        4: "Assemble the change",
        5: "Approve the start",
        6: "Execute the change",
        7: "Verify the result",
        8: "Review and decide",
        9: "Archive and carry forward",
    }
    return labels.get(step, str(step))
