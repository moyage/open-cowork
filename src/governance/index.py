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
    payload = {"current_change": change}
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
            changes[index] = {**current, **entry}
            break
    else:
        changes.append(entry)
    write_yaml(paths.changes_index_file(), data)
    return data
