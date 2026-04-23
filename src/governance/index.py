from __future__ import annotations

from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def ensure_governance_index(root: str | Path) -> dict:
    paths = GovernancePaths(Path(root))
    paths.governance_dir.mkdir(parents=True, exist_ok=True)
    paths.index_dir.mkdir(parents=True, exist_ok=True)
    paths.changes_dir.mkdir(parents=True, exist_ok=True)
    paths.archive_dir.mkdir(parents=True, exist_ok=True)
    paths.governance_dir.joinpath("templates").mkdir(parents=True, exist_ok=True)
    if not paths.current_change_file().exists():
        write_yaml(paths.current_change_file(), {
            "schema": "current-change/v1",
            "status": "idle",
            "current_change": None,
            "note": "No active governance change.",
        })
    if not paths.changes_index_file().exists():
        write_yaml(paths.changes_index_file(), {"schema": "changes-index/v1", "changes": []})
    if not paths.maintenance_status_file().exists():
        write_yaml(paths.maintenance_status_file(), {
            "schema": "maintenance-status/v1",
            "status": "idle",
            "current_change_active": "none",
            "current_change_id": None,
            "last_archived_change": None,
            "last_archive_at": None,
            "residual_followups": [],
        })
    if not paths.archive_map_file().exists():
        write_yaml(paths.archive_map_file(), {"schema": "archive-map/v1", "archives": []})
    return {"current_change": read_current_change(root), "changes_index": read_changes_index(root)}


def read_current_change(root: str | Path) -> dict:
    return load_yaml(GovernancePaths(Path(root)).current_change_file())


def set_current_change(root: str | Path, change: dict) -> dict:
    paths = GovernancePaths(Path(root))
    current = load_yaml(paths.current_change_file())
    _ensure_non_regressive_change_state(
        existing_change_id=current.get("current_change_id") or (current.get("current_change") or {}).get("change_id"),
        existing_status=current.get("status") or (current.get("current_change") or {}).get("status"),
        existing_step=current.get("current_step") or (current.get("current_change") or {}).get("current_step"),
        incoming_change_id=change.get("change_id") or change.get("current_change_id"),
        incoming_status=change.get("status"),
        incoming_step=change.get("current_step"),
    )
    payload = {
        "schema": "current-change/v1",
        "status": change.get("status"),
        "current_change_id": change.get("change_id") or change.get("current_change_id"),
        "current_step": change.get("current_step"),
        "formal_dispatch_status": change.get("formal_dispatch_status"),
        "current_change": change,
    }
    write_yaml(paths.current_change_file(), payload)
    return payload


def read_changes_index(root: str | Path) -> dict:
    return load_yaml(GovernancePaths(Path(root)).changes_index_file())


def upsert_change_entry(root: str | Path, entry: dict) -> dict:
    paths = GovernancePaths(Path(root))
    data = read_changes_index(root)
    changes = data.setdefault("changes", [])
    for index, current in enumerate(changes):
        if current.get("change_id") == entry.get("change_id"):
            _ensure_non_regressive_change_state(
                existing_change_id=current.get("change_id"),
                existing_status=current.get("status"),
                existing_step=current.get("current_step"),
                incoming_change_id=entry.get("change_id"),
                incoming_status=entry.get("status"),
                incoming_step=entry.get("current_step"),
            )
            changes[index] = {**current, **entry}
            break
    else:
        changes.append(entry)
    write_yaml(paths.changes_index_file(), data)
    return data


def set_maintenance_status(root: str | Path, **updates) -> dict:
    paths = GovernancePaths(Path(root))
    current = load_yaml(paths.maintenance_status_file())
    _ensure_non_regressive_maintenance_status(current, updates)
    _ensure_sticky_archive_baseline(current, updates)
    _ensure_archive_baseline_resolves_in_archive_map(paths, current, updates)
    merged = {**current, **updates}
    write_yaml(paths.maintenance_status_file(), merged)
    return merged


_STATUS_RANKS = {
    "drafting": 10,
    "step6-executed-pre-step7": 20,
    "step7-blocked": 30,
    "step7-verified": 40,
    "review-revise": 50,
    "review-rejected": 60,
    "review-approved": 70,
    "archived": 80,
}


def _ensure_non_regressive_change_state(
    *,
    existing_change_id,
    existing_status,
    existing_step,
    incoming_change_id,
    incoming_status,
    incoming_step,
) -> None:
    if not existing_change_id or not incoming_change_id:
        return
    if str(existing_change_id) != str(incoming_change_id):
        return

    normalized_existing_step = _normalize_step(existing_step)
    normalized_incoming_step = _normalize_step(incoming_step)
    if normalized_existing_step is None or normalized_incoming_step is None:
        return
    if normalized_incoming_step < normalized_existing_step:
        raise ValueError(
            f"change '{incoming_change_id}' cannot regress from step {normalized_existing_step} to step {normalized_incoming_step}"
        )
    if normalized_incoming_step > normalized_existing_step:
        return

    existing_rank = _STATUS_RANKS.get(str(existing_status))
    incoming_rank = _STATUS_RANKS.get(str(incoming_status))
    if existing_rank is None or incoming_rank is None:
        return
    if incoming_rank < existing_rank:
        raise ValueError(
            f"change '{incoming_change_id}' cannot regress status from '{existing_status}' to '{incoming_status}'"
        )


def _normalize_step(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ensure_non_regressive_maintenance_status(current: dict, updates: dict) -> None:
    existing_change_id = current.get("current_change_id")
    incoming_change_id = updates.get("current_change_id", existing_change_id)

    if existing_change_id and incoming_change_id and str(existing_change_id) == str(incoming_change_id):
        existing_status = current.get("status")
        incoming_status = updates.get("status", existing_status)
        _ensure_non_regressive_status_pair(
            change_id=incoming_change_id,
            existing_status=existing_status,
            incoming_status=incoming_status,
        )

        existing_active = current.get("current_change_active")
        incoming_active = updates.get("current_change_active", existing_active)
        _ensure_non_regressive_status_pair(
            change_id=incoming_change_id,
            existing_status=existing_active,
            incoming_status=incoming_active,
        )

    if (
        updates.get("current_change_id") is None
        and updates.get("status") == "idle"
        and updates.get("current_change_active") == "none"
    ):
        return


def _ensure_non_regressive_status_pair(*, change_id, existing_status, incoming_status) -> None:
    existing_rank = _status_rank(existing_status)
    incoming_rank = _status_rank(incoming_status)
    if existing_rank is None or incoming_rank is None:
        return
    if incoming_rank < existing_rank:
        raise ValueError(
            f"maintenance-status for change '{change_id}' cannot regress from '{existing_status}' to '{incoming_status}'"
        )


def _ensure_sticky_archive_baseline(current: dict, updates: dict) -> None:
    if current.get("last_archived_change") is not None and "last_archived_change" in updates and updates.get("last_archived_change") is None:
        raise ValueError("maintenance-status cannot clear last_archived_change once established")
    if current.get("last_archive_at") is not None and "last_archive_at" in updates and updates.get("last_archive_at") is None:
        raise ValueError("maintenance-status cannot clear last_archive_at once established")


def _ensure_archive_baseline_resolves_in_archive_map(paths: GovernancePaths, current: dict, updates: dict) -> None:
    if "last_archived_change" not in updates and "last_archive_at" not in updates:
        return

    target_change_id = updates.get("last_archived_change", current.get("last_archived_change"))
    target_archived_at = updates.get("last_archive_at", current.get("last_archive_at"))
    if not target_change_id:
        return

    archive_map = load_yaml(paths.archive_map_file())
    archive_entry = _find_archive_entry_by_change_id(archive_map, str(target_change_id))
    if not archive_entry:
        raise ValueError(f"maintenance-status last_archived_change '{target_change_id}' is missing from archive-map")

    mapped_archived_at = archive_entry.get("archived_at")
    if target_archived_at and mapped_archived_at and str(target_archived_at) != str(mapped_archived_at):
        raise ValueError(
            f"maintenance-status last_archive_at '{target_archived_at}' does not match archive-map '{mapped_archived_at}'"
        )


def _status_rank(value):
    if value in (None, ""):
        return None
    normalized = str(value)
    if normalized == "draft":
        normalized = "drafting"
    if normalized == "none":
        normalized = "idle"
    return _STATUS_RANKS.get(normalized, 0 if normalized == "idle" else None)


def _find_archive_entry_by_change_id(archive_map: dict, change_id: str) -> dict:
    for entry in archive_map.get("archives", []):
        if str(entry.get("change_id")) == str(change_id):
            return entry
    return {}
