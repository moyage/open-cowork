from __future__ import annotations

from datetime import datetime, timezone
import shutil
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
CLOSEOUT_PACKET_SCHEMA = "closeout-packet/v1"
SYNC_PACKET_SCHEMA = "sync-packet/v1"
SYNC_HISTORY_SCHEMA = "sync-history/v1"
SYNC_EXPORT_MANIFEST_SCHEMA = "sync-export-manifest/v1"
CONTINUITY_DIGEST_SCHEMA = "continuity-digest/v1"


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
    }
    _append_existing_ref(refs, "runtime_timeline", paths.runtime_timeline_month_file(), paths.root)
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


def resolve_closeout_packet(
    root: str | Path,
    *,
    change_id: str,
    closeout_statement: str,
    delivered_scope: list[str],
    deferred_scope: list[str],
    key_outcomes: list[str],
    unresolved_items: list[str],
    next_direction: str,
    attention_points: list[str],
    carry_forward_items: list[str],
    operator_summary: str,
    sponsor_summary: str,
) -> dict:
    paths = GovernancePaths(Path(root))
    archive_dir = paths.archived_change_dir(change_id)
    receipt_path = archive_dir / "archive-receipt.yaml"
    manifest_path = archive_dir / "manifest.yaml"
    contract_path = archive_dir / "contract.yaml"
    verify_path = archive_dir / "verify.yaml"
    review_path = archive_dir / "review.yaml"

    if not receipt_path.exists():
        raise ValueError(f"archived change '{change_id}' is missing archive-receipt.yaml")
    if not manifest_path.exists():
        raise ValueError(f"archived change '{change_id}' is missing manifest.yaml")
    if not verify_path.exists():
        raise ValueError(f"archived change '{change_id}' is missing verify.yaml")
    if not review_path.exists():
        raise ValueError(f"archived change '{change_id}' is missing review.yaml")

    receipt = load_yaml(receipt_path)
    if not receipt.get("archive_executed"):
        raise ValueError(f"change '{change_id}' is not archived")
    _resolve_archived_change_anchor(paths, change_id, receipt)

    manifest = load_yaml(manifest_path)
    verify_payload = load_yaml(verify_path)
    review_payload = load_yaml(review_path)
    maintenance = _load_optional_yaml(paths.maintenance_status_file())

    refs = {
        "archive_receipt": str(receipt_path.relative_to(paths.root)),
        "archived_manifest": str(manifest_path.relative_to(paths.root)),
        "archived_contract": str(contract_path.relative_to(paths.root)) if contract_path.exists() else None,
        "archived_verify": str(verify_path.relative_to(paths.root)),
        "archived_review": str(review_path.relative_to(paths.root)),
    }
    refs = {key: value for key, value in refs.items() if value is not None}
    _append_existing_ref(refs, "maintenance_status", paths.maintenance_status_file(), paths.root)
    _append_existing_ref(refs, "runtime_timeline", paths.runtime_timeline_month_file(), paths.root)
    runtime_change_status_ref = _runtime_change_status_ref_if_matching(paths, change_id)
    if runtime_change_status_ref:
        refs["runtime_change_status"] = runtime_change_status_ref
    _append_optional_closeout_ref(refs, "handoff_package", paths.handoff_package_file(change_id), paths.root)
    _append_optional_closeout_ref(refs, "owner_transfer", paths.owner_transfer_continuity_file(change_id), paths.root)
    _append_optional_closeout_ref(refs, "increment_package", paths.increment_package_file(change_id), paths.root)

    archived_at = receipt.get("archived_at") or _now_utc()
    final_step = manifest.get("current_step", 9)
    final_status = manifest.get("status", "archived")
    final_decision = review_payload.get("decision", {}).get("status")
    if final_decision == "approve":
        final_decision = "approve-and-close"

    return {
        "schema": CLOSEOUT_PACKET_SCHEMA,
        "change_id": change_id,
        "generated_at": _now_utc(),
        "closeout_kind": "archived-change",
        "closure_summary": {
            "title": manifest.get("title"),
            "final_status": final_status,
            "final_phase": _phase_label_for_step(final_step),
            "final_step": final_step,
            "final_decision": final_decision,
            "closeout_statement": closeout_statement,
            "archived_at": archived_at,
            "verify_status": verify_payload.get("summary", {}).get("status"),
        },
        "result_summary": {
            "delivered_scope": list(delivered_scope),
            "deferred_scope": list(deferred_scope),
            "key_outcomes": list(key_outcomes),
            "unresolved_items": list(unresolved_items),
        },
        "continuity_bridge": {
            "next_round_default_direction": next_direction,
            "next_round_attention_points": list(attention_points),
            "carry_forward_items": list(carry_forward_items),
        },
        "human_reading_entry": {
            "operator_summary": operator_summary,
            "sponsor_summary": sponsor_summary,
            "next_operator_start_pack": [
                str(paths.closeout_packet_file(change_id).relative_to(paths.root)),
                str(receipt_path.relative_to(paths.root)),
                str(review_path.relative_to(paths.root)),
            ],
        },
        "refs": refs,
        "maintenance_anchor": {
            "last_archived_change": maintenance.get("last_archived_change"),
            "last_archive_at": maintenance.get("last_archive_at"),
        },
    }


def materialize_closeout_packet(
    root: str | Path,
    *,
    change_id: str,
    closeout_statement: str,
    delivered_scope: list[str],
    deferred_scope: list[str],
    key_outcomes: list[str],
    unresolved_items: list[str],
    next_direction: str,
    attention_points: list[str],
    carry_forward_items: list[str],
    operator_summary: str,
    sponsor_summary: str,
) -> str:
    payload = resolve_closeout_packet(
        root,
        change_id=change_id,
        closeout_statement=closeout_statement,
        delivered_scope=delivered_scope,
        deferred_scope=deferred_scope,
        key_outcomes=key_outcomes,
        unresolved_items=unresolved_items,
        next_direction=next_direction,
        attention_points=attention_points,
        carry_forward_items=carry_forward_items,
        operator_summary=operator_summary,
        sponsor_summary=sponsor_summary,
    )
    target = GovernancePaths(Path(root)).closeout_packet_file(change_id)
    write_yaml(target, payload)
    return str(target)


def resolve_sync_packet(
    root: str | Path,
    *,
    change_id: str,
    source_kind: str,
    sync_kind: str,
    target_layer: str,
    target_scope: str,
    urgency: str,
    headline: str,
    delivered_scope: list[str],
    pending_scope: list[str],
    requested_attention: list[str],
    requested_decisions: list[str],
    next_owner_suggestion: str,
    next_action_suggestion: str,
) -> dict:
    paths = GovernancePaths(Path(root))
    if source_kind not in {"closeout", "increment"}:
        raise ValueError("source_kind must be 'closeout' or 'increment'")
    if sync_kind not in {"routine-sync", "escalation"}:
        raise ValueError("sync_kind must be 'routine-sync' or 'escalation'")
    if sync_kind == "escalation" and not (requested_attention or requested_decisions):
        raise ValueError("escalation sync requires requested attention or requested decisions")

    if source_kind == "closeout":
        source_path = paths.closeout_packet_file(change_id)
        receipt_path = paths.archived_change_file(change_id, "archive-receipt.yaml")
        if not receipt_path.exists():
            raise ValueError(f"archived change '{change_id}' is missing archive-receipt.yaml")
        receipt = load_yaml(receipt_path)
        if not receipt.get("archive_executed"):
            raise ValueError(f"change '{change_id}' is not archived")
        _resolve_archived_change_anchor(paths, change_id, receipt)
    else:
        source_path = paths.increment_package_file(change_id)
    if not source_path.exists():
        raise ValueError(f"{source_kind} source for '{change_id}' does not exist")

    source_payload = load_yaml(source_path)
    refs = {f"{source_kind}_packet": str(source_path.relative_to(paths.root))}

    runtime_timeline_ref = source_payload.get("refs", {}).get("runtime_timeline")
    _append_resolved_payload_ref(refs, "runtime_timeline", runtime_timeline_ref, paths.root)
    owner_transfer_path = paths.owner_transfer_continuity_file(change_id)
    if owner_transfer_path.exists():
        refs["owner_transfer"] = str(owner_transfer_path.relative_to(paths.root))

    source_status, source_summary = _sync_source_summary(source_kind, source_payload)

    return {
        "schema": SYNC_PACKET_SCHEMA,
        "change_id": change_id,
        "generated_at": _now_utc(),
        "sync_kind": sync_kind,
        "source_anchor": {
            "source_kind": source_kind,
            "source_ref": str(source_path.relative_to(paths.root)),
            "source_status": source_status,
            "source_summary": source_summary,
        },
        "target_context": {
            "target_layer": target_layer,
            "target_scope": target_scope,
            "urgency": urgency,
        },
        "sync_summary": {
            "headline": headline,
            "delivered_scope": list(delivered_scope),
            "pending_scope": list(pending_scope),
            "requested_attention": list(requested_attention),
            "requested_decisions": list(requested_decisions),
        },
        "continuity_bridge": {
            "next_owner_suggestion": next_owner_suggestion,
            "next_action_suggestion": next_action_suggestion,
            "return_path_ref": str(source_path.relative_to(paths.root)),
        },
        "refs": refs,
    }


def materialize_sync_packet(
    root: str | Path,
    *,
    change_id: str,
    source_kind: str,
    sync_kind: str,
    target_layer: str,
    target_scope: str,
    urgency: str,
    headline: str,
    delivered_scope: list[str],
    pending_scope: list[str],
    requested_attention: list[str],
    requested_decisions: list[str],
    next_owner_suggestion: str,
    next_action_suggestion: str,
) -> str:
    payload = resolve_sync_packet(
        root,
        change_id=change_id,
        source_kind=source_kind,
        sync_kind=sync_kind,
        target_layer=target_layer,
        target_scope=target_scope,
        urgency=urgency,
        headline=headline,
        delivered_scope=delivered_scope,
        pending_scope=pending_scope,
        requested_attention=requested_attention,
        requested_decisions=requested_decisions,
        next_owner_suggestion=next_owner_suggestion,
        next_action_suggestion=next_action_suggestion,
    )
    target = GovernancePaths(Path(root)).sync_packet_file(change_id, source_kind=source_kind)
    write_yaml(target, payload)
    return str(target)


def append_sync_history(root: str | Path, *, change_id: str, source_kind: str) -> str:
    paths = GovernancePaths(Path(root))
    packet_path = paths.sync_packet_file(change_id, source_kind=source_kind)
    if not packet_path.exists():
        raise ValueError(f"sync packet for '{change_id}' does not exist")
    packet = load_yaml(packet_path)
    recorded_at = packet.get("generated_at") or _now_utc()
    month_key = recorded_at[:7].replace("-", "")
    target = paths.sync_history_month_file(month_key)
    current = load_yaml(target) if target.exists() else {
        "schema": SYNC_HISTORY_SCHEMA,
        "month": month_key,
        "events": [],
    }
    event = {
        "event_id": f"{change_id}-sync-{recorded_at.replace('-', '').replace(':', '')}",
        "change_id": change_id,
        "recorded_at": recorded_at,
        "sync_kind": packet.get("sync_kind"),
        "source_kind": source_kind,
        "target_layer": packet.get("target_context", {}).get("target_layer"),
        "target_scope": packet.get("target_context", {}).get("target_scope"),
        "packet_ref": str(packet_path.relative_to(paths.root)),
        "headline": packet.get("sync_summary", {}).get("headline"),
    }
    current["events"] = _merge_sync_history_events(current.get("events", []), event)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(target, current)
    return str(target)


def read_sync_history(
    root: str | Path,
    *,
    month: str,
    change_id: str | None = None,
    source_kind: str | None = None,
    sync_kind: str | None = None,
    summary_by: str | None = None,
    summary_only: bool = False,
) -> dict:
    paths = GovernancePaths(Path(root))
    target = paths.sync_history_month_file(month)
    current = load_yaml(target) if target.exists() else {
        "schema": SYNC_HISTORY_SCHEMA,
        "month": month,
        "events": [],
    }
    events = list(current.get("events", []))
    filtered = [
        event for event in events
        if (change_id is None or event.get("change_id") == change_id)
        and (source_kind is None or event.get("source_kind") == source_kind)
        and (sync_kind is None or event.get("sync_kind") == sync_kind)
    ]
    payload = {
        "schema": "sync-history-query/v1",
        "month": month,
        "filters": {
            "change_id": change_id,
            "source_kind": source_kind,
            "sync_kind": sync_kind,
        },
        "summary": {
            "total_events": len(events),
            "matched_events": len(filtered),
        },
        "events": filtered,
    }
    if summary_by is not None:
        payload["grouped_summary"] = _group_sync_history_events(filtered, summary_by)
    if summary_only:
        payload["events"] = []
    return payload


def list_sync_history_months(root: str | Path) -> list[str]:
    paths = GovernancePaths(Path(root))
    if not paths.sync_history_dir.exists():
        return []
    months = []
    for path in paths.sync_history_dir.glob("events-*.yaml"):
        name = path.stem
        if name.startswith("events-"):
            months.append(name.removeprefix("events-"))
    return sorted(set(months))


def read_sync_history_across_months(
    root: str | Path,
    *,
    change_id: str | None = None,
    source_kind: str | None = None,
    sync_kind: str | None = None,
    summary_by: str | None = None,
    summary_only: bool = False,
) -> dict:
    paths = GovernancePaths(Path(root))
    months = list_sync_history_months(root)
    events = []
    total_events = 0
    for month in months:
        target = paths.sync_history_month_file(month)
        current = load_yaml(target) if target.exists() else {"events": []}
        month_events = list(current.get("events", []))
        total_events += len(month_events)
        events.extend(month_events)
    filtered = [
        event for event in events
        if (change_id is None or event.get("change_id") == change_id)
        and (source_kind is None or event.get("source_kind") == source_kind)
        and (sync_kind is None or event.get("sync_kind") == sync_kind)
    ]
    filtered.sort(key=lambda item: str(item.get("recorded_at") or ""))
    payload = {
        "schema": "sync-history-query/v1",
        "month": "all",
        "months": months,
        "filters": {
            "change_id": change_id,
            "source_kind": source_kind,
            "sync_kind": sync_kind,
        },
        "summary": {
            "total_events": total_events,
            "matched_events": len(filtered),
        },
        "events": filtered,
    }
    if summary_by is not None:
        payload["grouped_summary"] = _group_sync_history_events(filtered, summary_by)
    if summary_only:
        payload["events"] = []
    return payload


def _group_sync_history_events(events: list[dict], group_by: str) -> dict:
    groups: dict[str, dict] = {}
    for event in events:
        key = str(event.get(group_by) or "unknown")
        existing = groups.get(key)
        if existing is None:
            groups[key] = {
                "group_key": key,
                "event_count": 1,
                "latest_recorded_at": event.get("recorded_at"),
                "latest_headline": event.get("headline"),
                "latest_change_id": event.get("change_id"),
                "latest_sync_kind": event.get("sync_kind"),
            }
            continue
        existing["event_count"] += 1
        if str(event.get("recorded_at") or "") >= str(existing.get("latest_recorded_at") or ""):
            existing["latest_recorded_at"] = event.get("recorded_at")
            existing["latest_headline"] = event.get("headline")
            existing["latest_change_id"] = event.get("change_id")
            existing["latest_sync_kind"] = event.get("sync_kind")
    ordered = sorted(
        groups.values(),
        key=lambda item: (-int(item.get("event_count") or 0), str(item.get("group_key") or "")),
    )
    return {
        "group_by": group_by,
        "groups": ordered,
    }


def export_sync_packet(root: str | Path, *, change_id: str, source_kind: str, output_dir: str | Path) -> str:
    paths = GovernancePaths(Path(root))
    packet_path = paths.sync_packet_file(change_id, source_kind=source_kind)
    if not packet_path.exists():
        raise ValueError(f"sync packet for '{change_id}' does not exist")
    packet = load_yaml(packet_path)
    export_root = Path(output_dir)
    export_target = export_root / change_id
    export_target.mkdir(parents=True, exist_ok=True)

    shutil.copy2(packet_path, export_target / "sync-packet.yaml")
    manifest = {
        "schema": SYNC_EXPORT_MANIFEST_SCHEMA,
        "change_id": change_id,
        "exported_at": _now_utc(),
        "source_sync_packet": str(packet_path.relative_to(paths.root)),
        "export_dir": str(export_target),
        "files": ["README.md", "export-manifest.yaml", "sync-packet.yaml"],
    }
    write_yaml(export_target / "export-manifest.yaml", manifest)
    (export_target / "README.md").write_text(
        _render_sync_export_readme(change_id, packet, manifest),
        encoding="utf-8",
    )
    return str(export_target)


def resolve_continuity_digest(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    resolved_change_id, selected_by, digest_kind = _select_digest_change(paths, change_id)
    if digest_kind == "active":
        return _resolve_active_continuity_digest(paths, resolved_change_id, selected_by)
    return _resolve_archived_continuity_digest(paths, resolved_change_id, selected_by)


def _path_ref(paths: GovernancePaths, change_id: str, name: str) -> dict:
    return {
        "path": str(paths.change_file(change_id, name).relative_to(paths.root)),
        "role": name,
    }


def _select_digest_change(paths: GovernancePaths, change_id: str | None) -> tuple[str, str, str]:
    if change_id:
        if paths.change_file(change_id, "manifest.yaml").exists():
            return str(change_id), "explicit-change-id", "active"
        if paths.archived_change_file(change_id, "manifest.yaml").exists():
            return str(change_id), "explicit-change-id", "archived"
        raise ValueError(f"change '{change_id}' does not exist in active or archived space")

    current_payload = read_current_change(paths.root)
    current_change_id = _extract_current_change_id(current_payload)
    if current_change_id and paths.change_file(str(current_change_id), "manifest.yaml").exists():
        return str(current_change_id), "current-change", "active"

    maintenance = _load_optional_yaml(paths.maintenance_status_file())
    last_archived_change = maintenance.get("last_archived_change")
    if last_archived_change and paths.archived_change_file(str(last_archived_change), "manifest.yaml").exists():
        return str(last_archived_change), "last-archived-change", "archived"

    raise ValueError("no active change or archived baseline available for continuity digest")


def _resolve_active_continuity_digest(paths: GovernancePaths, change_id: str, selected_by: str) -> dict:
    runtime_payload = _ensure_runtime_status_payload(paths, change_id)
    manifest = _load_change_manifest(paths, change_id)
    handoff_ref = _ref_path_if_exists(paths.root, str(paths.handoff_package_file(change_id).relative_to(paths.root)))
    increment_ref = _ref_path_if_exists(paths.root, str(paths.increment_package_file(change_id).relative_to(paths.root)))
    owner_transfer_ref = _ref_path_if_exists(
        paths.root,
        str(paths.owner_transfer_continuity_file(change_id).relative_to(paths.root)),
    )
    sync_ref = _ref_path_if_exists(
        paths.root,
        str(paths.sync_packet_file(change_id, source_kind="increment").relative_to(paths.root)),
    )

    refs = {}
    _append_resolved_payload_ref(refs, "handoff_package", handoff_ref, paths.root)
    _append_resolved_payload_ref(refs, "increment_package", increment_ref, paths.root)
    _append_resolved_payload_ref(refs, "owner_transfer", owner_transfer_ref, paths.root)
    _append_resolved_payload_ref(refs, "sync_packet", sync_ref, paths.root)
    refs["runtime_change_status"] = str(paths.runtime_change_status_file().relative_to(paths.root))
    refs["runtime_steps_status"] = str(paths.runtime_steps_status_file().relative_to(paths.root))

    primary_ref = refs.get("handoff_package") or refs["runtime_change_status"]
    secondary_refs = [
        ref for ref in [
            refs.get("increment_package"),
            refs.get("owner_transfer"),
            refs.get("sync_packet"),
            refs.get("runtime_steps_status"),
        ]
        if ref
    ]

    change_status = runtime_payload.get("change_status", {})
    gate_posture = change_status.get("gate_posture", {}) or {}
    payload = {
        "schema": CONTINUITY_DIGEST_SCHEMA,
        "change_id": change_id,
        "digest_kind": "active",
        "selected_by": selected_by,
        "generated_at": _now_utc(),
        "summary": {
            "title": manifest.get("title"),
            "status": change_status.get("current_status"),
            "phase": change_status.get("phase"),
            "step": change_status.get("current_step"),
            "headline": manifest.get("title") or change_id,
            "next_attention": gate_posture.get("waiting_on") or gate_posture.get("next_decision"),
            "human_intervention_required": gate_posture.get("human_intervention_required"),
        },
        "recommended_reading": {
            "primary_ref": primary_ref,
            "secondary_refs": secondary_refs,
        },
        "projection_sources": _active_digest_projection_sources(paths, change_id),
        "refs": refs,
        "sync_view": {
            "available": bool(refs.get("sync_packet")),
            "sync_packet_ref": refs.get("sync_packet"),
        },
    }
    recent_sync_summary = _recent_sync_summary_for_change(paths.root, change_id)
    if recent_sync_summary:
        payload["recent_sync_summary"] = recent_sync_summary
    recent_runtime_events = _recent_runtime_events_for_change(paths, change_id)
    if recent_runtime_events:
        payload["recent_runtime_events"] = recent_runtime_events
    return payload


def _resolve_archived_continuity_digest(paths: GovernancePaths, change_id: str, selected_by: str) -> dict:
    closeout_ref = _ref_path_if_exists(paths.root, str(paths.closeout_packet_file(change_id).relative_to(paths.root)))
    review_ref = _ref_path_if_exists(paths.root, str(paths.archived_change_file(change_id, "review.yaml").relative_to(paths.root)))
    manifest_ref = _ref_path_if_exists(paths.root, str(paths.archived_change_file(change_id, "manifest.yaml").relative_to(paths.root)))
    sync_ref = _ref_path_if_exists(
        paths.root,
        str(paths.sync_packet_file(change_id, source_kind="closeout").relative_to(paths.root)),
    )

    manifest = _load_optional_yaml(paths.archived_change_file(change_id, "manifest.yaml"))
    review = _load_optional_yaml(paths.archived_change_file(change_id, "review.yaml"))
    closeout = _load_optional_yaml(paths.closeout_packet_file(change_id))

    refs = {}
    _append_resolved_payload_ref(refs, "closeout_packet", closeout_ref, paths.root)
    _append_resolved_payload_ref(refs, "archived_review", review_ref, paths.root)
    _append_resolved_payload_ref(refs, "archived_manifest", manifest_ref, paths.root)
    _append_resolved_payload_ref(refs, "sync_packet", sync_ref, paths.root)

    primary_ref = refs.get("closeout_packet") or refs.get("archived_review") or refs.get("archived_manifest")
    secondary_refs = [
        ref for ref in [
            refs.get("archived_review"),
            refs.get("archived_manifest"),
            refs.get("sync_packet"),
        ]
        if ref and ref != primary_ref
    ]

    closure_summary = closeout.get("closure_summary", {}) or {}
    human_reading_entry = closeout.get("human_reading_entry", {}) or {}
    payload = {
        "schema": CONTINUITY_DIGEST_SCHEMA,
        "change_id": change_id,
        "digest_kind": "archived",
        "selected_by": selected_by,
        "generated_at": _now_utc(),
        "summary": {
            "title": manifest.get("title"),
            "status": closure_summary.get("final_status") or manifest.get("status"),
            "phase": closure_summary.get("final_phase") or _phase_label_for_step(manifest.get("current_step")),
            "step": closure_summary.get("final_step") or manifest.get("current_step"),
            "headline": human_reading_entry.get("operator_summary") or closure_summary.get("closeout_statement") or manifest.get("title") or change_id,
            "next_attention": closeout.get("continuity_bridge", {}).get("next_round_default_direction"),
            "human_intervention_required": False,
        },
        "recommended_reading": {
            "primary_ref": primary_ref,
            "secondary_refs": secondary_refs,
        },
        "projection_sources": _archived_digest_projection_sources(paths, change_id),
        "refs": refs,
        "sync_view": {
            "available": bool(refs.get("sync_packet")),
            "sync_packet_ref": refs.get("sync_packet"),
            "review_status": review.get("decision", {}).get("status"),
        },
    }
    recent_sync_summary = _recent_sync_summary_for_change(paths.root, change_id)
    if recent_sync_summary:
        payload["recent_sync_summary"] = recent_sync_summary
    recent_runtime_events = _recent_runtime_events_for_change(paths, change_id)
    if recent_runtime_events:
        payload["recent_runtime_events"] = recent_runtime_events
    return payload


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


def _append_optional_closeout_ref(refs: dict, key: str, path: Path, root: Path) -> None:
    if path.exists():
        refs[key] = str(path.relative_to(root))


def _append_existing_ref(refs: dict, key: str, path: Path, root: Path) -> None:
    if path.exists():
        refs[key] = str(path.relative_to(root))


def _append_resolved_payload_ref(refs: dict, key: str, ref: str | None, root: Path) -> None:
    resolved = _ref_path_if_exists(root, ref)
    if resolved:
        refs[key] = resolved


def _ref_path_if_exists(root: Path, ref: str | None) -> str | None:
    if not ref or not isinstance(ref, str):
        return None
    candidate = (root / ref).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return ref if candidate.exists() else None


def _runtime_change_status_ref_if_matching(paths: GovernancePaths, change_id: str) -> str | None:
    status_path = paths.runtime_change_status_file()
    if not status_path.exists():
        return None
    payload = load_yaml(status_path)
    if payload.get("change_id") != change_id:
        return None
    return str(status_path.relative_to(paths.root))


def _merge_sync_history_events(existing: list[dict], new_event: dict) -> list[dict]:
    for item in existing:
        if item.get("packet_ref") == new_event.get("packet_ref"):
            return existing
    return list(existing) + [new_event]


def _recent_sync_summary_for_change(root: Path, change_id: str) -> dict | None:
    payload = read_sync_history_across_months(root, change_id=change_id)
    events = list(payload.get("events", []))
    if not events:
        return None
    latest = events[-1]
    return {
        "total_events": payload.get("summary", {}).get("matched_events", len(events)),
        "latest_recorded_at": latest.get("recorded_at"),
        "latest_source_kind": latest.get("source_kind"),
        "latest_sync_kind": latest.get("sync_kind"),
        "latest_target_layer": latest.get("target_layer"),
        "latest_headline": latest.get("headline"),
    }


def _recent_runtime_events_for_change(paths: GovernancePaths, change_id: str, limit: int = 3) -> list[dict]:
    timeline_path = paths.runtime_timeline_month_file()
    if not timeline_path.exists():
        return []
    payload = load_yaml(timeline_path)
    events = [
        {
            "event_type": event.get("event_type"),
            "step": event.get("step"),
            "to_status": event.get("to_status"),
            "timestamp": event.get("timestamp"),
        }
        for event in payload.get("events", [])
        if event.get("change_id") == change_id
    ]
    events.sort(key=lambda item: str(item.get("timestamp") or ""))
    return events[-limit:]


def _active_digest_projection_sources(paths: GovernancePaths, change_id: str) -> dict:
    manifest_ref = str(paths.change_file(change_id, "manifest.yaml").relative_to(paths.root))
    runtime_ref = str(paths.runtime_change_status_file().relative_to(paths.root))
    return {
        "summary": {
            "title": {"source_ref": manifest_ref, "source_field": "title"},
            "status": {"source_ref": runtime_ref, "source_field": "current_status"},
            "phase": {"source_ref": runtime_ref, "source_field": "phase"},
            "step": {"source_ref": runtime_ref, "source_field": "current_step"},
            "headline": {"source_ref": manifest_ref, "source_field": "title"},
            "next_attention": {
                "source_ref": runtime_ref,
                "source_field": "gate_posture.waiting_on|gate_posture.next_decision",
            },
        }
    }


def _archived_digest_projection_sources(paths: GovernancePaths, change_id: str) -> dict:
    manifest_ref = str(paths.archived_change_file(change_id, "manifest.yaml").relative_to(paths.root))
    closeout_ref = str(paths.closeout_packet_file(change_id).relative_to(paths.root))
    return {
        "summary": {
            "title": {"source_ref": manifest_ref, "source_field": "title"},
            "status": {"source_ref": closeout_ref, "source_field": "closure_summary.final_status"},
            "phase": {"source_ref": closeout_ref, "source_field": "closure_summary.final_phase"},
            "step": {"source_ref": closeout_ref, "source_field": "closure_summary.final_step"},
            "headline": {
                "source_ref": closeout_ref,
                "source_field": "human_reading_entry.operator_summary|closure_summary.closeout_statement",
            },
            "next_attention": {
                "source_ref": closeout_ref,
                "source_field": "continuity_bridge.next_round_default_direction",
            },
        }
    }


def _render_sync_export_readme(change_id: str, packet: dict, manifest: dict) -> str:
    return "\n".join([
        "# Sync Packet Export",
        "",
        f"- change_id: {change_id}",
        f"- sync_kind: {packet.get('sync_kind')}",
        f"- source_kind: {packet.get('source_anchor', {}).get('source_kind')}",
        f"- headline: {packet.get('sync_summary', {}).get('headline')}",
        f"- exported_at: {manifest.get('exported_at')}",
        "",
        "本目录是显式导出的上层消费包，不是项目内 authoritative truth-source。",
        "",
    ])


def _sync_source_summary(source_kind: str, payload: dict) -> tuple[str | None, str | None]:
    if source_kind == "closeout":
        closure = payload.get("closure_summary", {})
        return closure.get("final_status"), closure.get("closeout_statement")
    anchor = payload.get("state_anchor", {})
    return anchor.get("current_status"), anchor.get("next_decision")


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


def _resolve_archived_change_anchor(paths: GovernancePaths, change_id: str, receipt: dict) -> dict:
    archive_map = load_yaml(paths.archive_map_file())
    try:
        entry = _find_archive_entry(archive_map, change_id)
    except ValueError as exc:
        raise ValueError(f"archived change '{change_id}' is missing from archive-map") from exc
    expected_archive_path = str(paths.archived_change_dir(change_id).relative_to(paths.root)) + "/"
    expected_receipt = str(paths.archived_change_file(change_id, "archive-receipt.yaml").relative_to(paths.root))
    if entry.get("archive_path") and str(entry.get("archive_path")) != expected_archive_path:
        raise ValueError(
            f"archived change '{change_id}' archive_path does not match archive-map"
        )
    if entry.get("receipt") and str(entry.get("receipt")) != expected_receipt:
        raise ValueError(
            f"archived change '{change_id}' receipt does not match archive-map"
        )
    mapped_archived_at = entry.get("archived_at")
    receipt_archived_at = receipt.get("archived_at")
    if mapped_archived_at and receipt_archived_at and str(mapped_archived_at) != str(receipt_archived_at):
        raise ValueError(
            f"archived change '{change_id}' archived_at does not match archive-map"
        )
    return entry


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
