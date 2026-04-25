from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .change_package import update_manifest
from .index import set_current_change, set_maintenance_status, upsert_change_entry
from .lifecycle import require_transition_state
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def archive_change(root: str | Path, change_id: str) -> dict:
    paths = GovernancePaths(Path(root))
    source_dir = paths.change_dir(change_id)
    archive_dir = paths.archived_change_dir(change_id)
    require_transition_state(
        root,
        change_id,
        expected_step=8,
        allowed_statuses=["review-approved"],
        action_label="archive",
    )
    review_payload = load_yaml(paths.change_file(change_id, "review.yaml"))
    if review_payload.get("decision", {}).get("status") != "approve":
        raise ValueError(f"change '{change_id}' must have an approved review before archive")
    archive_dir.mkdir(parents=True, exist_ok=True)

    manifest = update_manifest(root, change_id, status="archived", current_step=9)
    for child in source_dir.iterdir():
        target = archive_dir / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)

    archived_at = datetime.now(timezone.utc).isoformat()
    receipt = {
        "schema": "archive-receipt/v1",
        "change_id": change_id,
        "archive_executed": True,
        "archived_at": archived_at,
        "traceability": {
            "review": str(paths.archived_change_file(change_id, "review.yaml").relative_to(paths.root)),
            "manifest": str(paths.archived_change_file(change_id, "manifest.yaml").relative_to(paths.root)),
        },
        "residual_followups": [],
    }
    receipt_path = paths.archived_change_file(change_id, "archive-receipt.yaml")
    write_yaml(receipt_path, receipt)

    archive_map = load_yaml(paths.archive_map_file())
    archives = archive_map.setdefault("archives", [])
    entry = {
        "change_id": change_id,
        "archive_path": str(archive_dir.relative_to(paths.root)) + "/",
        "archived_at": archived_at,
        "receipt": str(receipt_path.relative_to(paths.root)),
    }
    for index, current in enumerate(archives):
        if current.get("change_id") == change_id:
            archives[index] = entry
            break
    else:
        archives.append(entry)
    write_yaml(paths.archive_map_file(), archive_map)

    set_current_change(root, {
        "change_id": None,
        "status": "idle",
        "current_step": None,
    })
    upsert_change_entry(root, {
        "change_id": change_id,
        "path": str(source_dir.relative_to(paths.root)),
        "status": "archived",
        "current_step": 9,
    })
    set_maintenance_status(
        root,
        status="idle",
        current_change_active="none",
        current_change_id=None,
        last_archived_change=change_id,
        last_archive_at=archived_at,
    )
    from .current_state import sync_current_state

    sync_current_state(root)
    return receipt
