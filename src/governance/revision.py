from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
from .lifecycle import require_transition_state
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def open_revision(root: str | Path, change_id: str, *, reason: str, recorded_by: str) -> dict:
    paths = GovernancePaths(Path(root))
    require_transition_state(root, change_id, expected_step=8, allowed_statuses=["review-revise"], action_label="revise")
    history_path = paths.change_file(change_id, "revision-history.yaml")
    history = load_yaml(history_path) if history_path.exists() else {"schema": "revision-history/v1", "change_id": change_id, "revisions": []}
    revisions = history.setdefault("revisions", [])
    revision_round = len(revisions) + 1
    revision = {
        "revision_round": revision_round,
        "reason": reason,
        "recorded_by": recorded_by,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "from_status": "review-revise",
        "to_status": "revision-open",
        "findings": _latest_review_findings(paths, change_id),
        "fix_evidence_required": _latest_fix_evidence_required(paths, change_id),
    }
    revisions.append(revision)
    write_yaml(history_path, history)
    _append_rework_round(paths, change_id, revision)

    manifest = update_manifest(
        root,
        change_id,
        status="revision-open",
        current_step=6,
        revision_round=revision_round,
        readiness={"step6_entry_ready": True, "missing_items": []},
    )
    current = read_current_change(root)
    current_change = current.get("current_change") or {}
    entry = {
        **current_change,
        "change_id": change_id,
        "path": str(paths.change_dir(change_id).relative_to(paths.root)),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
    }
    set_current_change(root, entry)
    upsert_change_entry(root, entry)
    set_maintenance_status(root, status=manifest.get("status"), current_change_active=manifest.get("status"), current_change_id=change_id)
    return {"change_id": change_id, "revision": revision, "history_ref": str(history_path.relative_to(paths.root)), "status": manifest.get("status"), "current_step": manifest.get("current_step")}


def _latest_review_findings(paths: GovernancePaths, change_id: str) -> list[dict]:
    latest = _latest_lifecycle_round(paths, change_id)
    findings = latest.get("blocking_findings", []) if latest else []
    return [{**finding, "source": "review-lifecycle.yaml"} for finding in findings]


def _latest_fix_evidence_required(paths: GovernancePaths, change_id: str) -> list[dict]:
    latest = _latest_lifecycle_round(paths, change_id)
    return latest.get("fix_evidence_required", []) if latest else []


def _latest_lifecycle_round(paths: GovernancePaths, change_id: str) -> dict:
    path = paths.change_file(change_id, "review-lifecycle.yaml")
    if not path.exists():
        return {}
    lifecycle = load_yaml(path)
    rounds = lifecycle.get("rounds", [])
    return rounds[-1] if rounds else {}


def _append_rework_round(paths: GovernancePaths, change_id: str, revision: dict) -> None:
    path = paths.change_file(change_id, "review-lifecycle.yaml")
    lifecycle = load_yaml(path) if path.exists() else {
        "schema": "review-lifecycle/v1",
        "change_id": change_id,
        "status": "changes-requested",
        "rounds": [],
        "rework_rounds": [],
    }
    rework_rounds = lifecycle.setdefault("rework_rounds", [])
    rework_rounds.append({
        "round": revision["revision_round"],
        "status": "revision-open",
        "reason": revision["reason"],
        "recorded_by": revision["recorded_by"],
        "recorded_at": revision["recorded_at"],
        "findings": revision.get("findings", []),
        "fix_evidence_required": revision.get("fix_evidence_required", []),
    })
    lifecycle["status"] = "rework-open"
    write_yaml(path, lifecycle)
