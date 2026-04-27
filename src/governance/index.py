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
    paths.local_dir.mkdir(parents=True, exist_ok=True)
    _ensure_governance_gitignore(paths)
    if not paths.current_change_file().exists():
        write_yaml(paths.current_change_file(), {
            "schema": "current-change/v1",
            "status": "idle",
            "current_change": None,
            "note": "No active governance change.",
        })
    if not paths.active_changes_file().exists():
        write_yaml(paths.active_changes_file(), {"schema": "active-changes/v1", "changes": []})
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


def rebuild_governance_index(root: str | Path) -> dict:
    paths = GovernancePaths(Path(root))
    ensure_governance_index(paths.root)
    changes = _entries_from_change_manifests(paths)
    archived_entries = _entries_from_archive_receipts(paths)
    archived_ids = {entry["change_id"] for entry in archived_entries}
    combined = _merge_change_entries(changes, archived_entries)
    active = [
        entry for entry in combined
        if entry.get("change_id") not in archived_ids
        and str(entry.get("status")) not in {"idle", "archived", "abandoned", "superseded", "none"}
    ]
    archive_map = {
        "schema": "archive-map/v1",
        "archives": [
            {
                "change_id": entry["change_id"],
                "archive_path": f".governance/archive/{entry['change_id']}/",
                "archived_at": entry.get("archived_at"),
                "receipt": f".governance/archive/{entry['change_id']}/archive-receipt.yaml",
            }
            for entry in archived_entries
        ],
    }
    write_yaml(paths.changes_index_file(), {"schema": "changes-index/v1", "changes": combined})
    write_yaml(paths.active_changes_file(), {"schema": "active-changes/v1", "changes": active})
    write_yaml(paths.archive_map_file(), archive_map)
    return {
        "schema": "index-rebuild/v1",
        "changes_count": len(combined),
        "active_count": len(active),
        "archive_count": len(archived_entries),
        "changes_index": str(paths.changes_index_file().relative_to(paths.root)),
        "active_changes": str(paths.active_changes_file().relative_to(paths.root)),
        "archive_map": str(paths.archive_map_file().relative_to(paths.root)),
    }


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
    _upsert_active_change(paths, payload.get("current_change") or payload)
    return payload


def read_active_changes(root: str | Path) -> dict:
    paths = GovernancePaths(Path(root))
    if not paths.active_changes_file().exists():
        return {"schema": "active-changes/v1", "changes": []}
    return load_yaml(paths.active_changes_file())


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
            _upsert_active_change(paths, changes[index])
            break
    else:
        changes.append(entry)
        _upsert_active_change(paths, entry)
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
    "intent-captured": 11,
    "awaiting-intent-confirmation": 11,
    "step1-ready": 12,
    "step2-ready": 14,
    "step3-ready": 16,
    "step4-in-progress": 18,
    "step5-prepared": 19,
    "step6-in-progress": 20,
    "revision-open": 20,
    "step6-executed-pre-step7": 20,
    "step6-revision-executed-pre-step7": 20,
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
    if str(existing_status) == "review-revise" and str(incoming_status) == "revision-open":
        return
    if str(existing_status) == "drafting" and str(incoming_status) == "step1-ready":
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


def _ensure_governance_gitignore(paths: GovernancePaths) -> None:
    target = paths.governance_dir / ".gitignore"
    required = ["/local/", "/PROJECT_ACTIVATION.yaml", "/current-state.md", "/runtime/status/"]
    if target.exists():
        existing = target.read_text(encoding="utf-8").splitlines()
    else:
        existing = []
    merged = list(existing)
    for item in required:
        if item not in merged:
            merged.append(item)
    target.write_text("\n".join(merged).rstrip() + "\n", encoding="utf-8")


def _entries_from_change_manifests(paths: GovernancePaths) -> list[dict]:
    entries = []
    if not paths.changes_dir.exists():
        return entries
    for manifest_path in sorted(paths.changes_dir.glob("*/manifest.yaml")):
        manifest = load_yaml(manifest_path)
        change_id = str(manifest.get("change_id") or manifest_path.parent.name)
        entries.append({
            "change_id": change_id,
            "path": str(manifest_path.parent.relative_to(paths.root)),
            "status": manifest.get("status") or "drafting",
            "current_step": manifest.get("current_step"),
            "title": manifest.get("title"),
            "owner": manifest.get("owner"),
        })
    return entries


def _entries_from_archive_receipts(paths: GovernancePaths) -> list[dict]:
    entries = []
    if not paths.archive_dir.exists():
        return entries
    for receipt_path in sorted(paths.archive_dir.glob("*/archive-receipt.yaml")):
        receipt = load_yaml(receipt_path)
        archive_dir = receipt_path.parent
        manifest_path = archive_dir / "manifest.yaml"
        manifest = load_yaml(manifest_path) if manifest_path.exists() else {}
        change_id = str(receipt.get("change_id") or manifest.get("change_id") or archive_dir.name)
        entries.append({
            "change_id": change_id,
            "path": f".governance/archive/{change_id}",
            "status": "archived",
            "current_step": manifest.get("current_step") or 9,
            "title": manifest.get("title") or change_id,
            "owner": manifest.get("owner"),
            "archived_at": receipt.get("archived_at"),
        })
    return entries


def _merge_change_entries(active_entries: list[dict], archived_entries: list[dict]) -> list[dict]:
    by_id = {}
    for entry in active_entries:
        by_id[entry["change_id"]] = entry
    for entry in archived_entries:
        by_id[entry["change_id"]] = {
            key: value for key, value in entry.items()
            if key != "archived_at"
        }
    return [by_id[key] for key in sorted(by_id)]


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
    if str(existing_status) == "review-revise" and str(incoming_status) == "revision-open":
        return
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


_TERMINAL_ACTIVE_STATUSES = {"idle", "archived", "abandoned", "superseded", "none", None}


def _upsert_active_change(paths: GovernancePaths, entry: dict) -> None:
    change_id = entry.get("change_id") or entry.get("current_change_id")
    status = entry.get("status")
    if not change_id:
        return
    data = read_active_changes(paths.root)
    changes = data.setdefault("changes", [])
    next_changes = [item for item in changes if str(item.get("change_id")) != str(change_id)]
    if status not in _TERMINAL_ACTIVE_STATUSES:
        next_changes.append({
            "change_id": str(change_id),
            "path": entry.get("path") or f".governance/changes/{change_id}",
            "status": status,
            "current_step": entry.get("current_step"),
            "title": entry.get("title"),
            "owner": entry.get("owner"),
        })
    data["changes"] = sorted(next_changes, key=lambda item: str(item.get("change_id")))
    write_yaml(paths.active_changes_file(), data)
