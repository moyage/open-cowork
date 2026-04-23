from __future__ import annotations

from pathlib import Path

from .index import read_changes_index, read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml

CONTINUITY_LAUNCH_INPUT_SCHEMA = "continuity-launch-input/v1"
ROUND_ENTRY_INPUT_SUMMARY_SCHEMA = "round-entry-input-summary/v1"


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


def _find_archive_entry(archive_map: dict, change_id: str) -> dict:
    for entry in archive_map.get("archives", []):
        if entry.get("change_id") == change_id:
            return entry
    raise ValueError(f"archived change '{change_id}' not found in archive map")
