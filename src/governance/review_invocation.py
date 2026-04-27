from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .change_package import read_change_package
from .simple_yaml import load_yaml, write_yaml


VALID_STATUSES = {"started", "running", "completed", "failed", "timeout"}


def record_review_invocation(
    root: str | Path,
    *,
    change_id: str,
    status: str,
    reviewer: str,
    runtime: str = "",
    note: str = "",
    timeout_policy: str = "",
    artifact_ref: str = "",
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    package = read_change_package(root, change_id)
    path = package.path / "review-invocation.yaml"
    payload = load_yaml(path) if path.exists() else {
        "schema": "review-invocation/v1",
        "change_id": change_id,
        "events": [],
    }
    now = _now_utc()
    event = {
        "status": status,
        "reviewer": reviewer,
        "runtime": runtime,
        "recorded_at": now,
        "note": note,
    }
    if artifact_ref:
        event["artifact_ref"] = artifact_ref
    payload.update({
        "status": status,
        "reviewer": reviewer,
        "runtime": runtime or payload.get("runtime"),
        "last_heartbeat_at": now,
        "timeout_policy": timeout_policy or payload.get("timeout_policy") or "",
    })
    if artifact_ref:
        payload["artifact_ref"] = artifact_ref
    payload.setdefault("events", []).append(event)
    write_yaml(path, payload)
    return payload


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
