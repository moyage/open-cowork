from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml


def append_runtime_event(
    root: str | Path,
    *,
    change_id: str,
    event_type: str,
    step: int,
    from_status: str | None,
    to_status: str | None,
    actor_id: str | None,
    refs: list[str] | None = None,
    source_path: str | Path | None = None,
    event_suffix: str | None = None,
    extra: dict | None = None,
) -> dict:
    paths = GovernancePaths(Path(root))
    paths.runtime_timeline_dir.mkdir(parents=True, exist_ok=True)
    target = paths.runtime_timeline_month_file()
    payload = load_yaml(target) if target.exists() else {
        "schema": "runtime-timeline/v1",
        "month": datetime.now(timezone.utc).strftime("%Y%m"),
        "events": [],
        "generated_at": _now_utc(),
    }
    event_id = _next_instance_event_id(
        payload.get("events", []),
        change_id=change_id,
        event_type=event_type,
        event_suffix=event_suffix,
    )
    event = {
        "schema": "runtime-event/v1",
        "event_id": event_id,
        "change_id": change_id,
        "entity_type": "change",
        "event_type": event_type,
        "step": step,
        "from_status": from_status,
        "to_status": to_status,
        "actor_id": actor_id or "governance",
        "timestamp": _event_timestamp(Path(source_path)) if source_path else _now_utc(),
        "refs": {"files": list(refs or [])},
    }
    if extra:
        event.update(extra)
    payload["events"] = _merge_events(payload.get("events", []), [event])
    payload["generated_at"] = _now_utc()
    write_yaml(target, payload)
    return event


def merge_runtime_timeline_payload(existing: dict, new_payload: dict) -> dict:
    merged_events = _merge_events(existing.get("events", []), new_payload.get("events", []))
    return {
        "schema": "runtime-timeline/v1",
        "month": new_payload.get("month") or existing.get("month"),
        "events": merged_events,
        "generated_at": _now_utc(),
    }


def _merge_events(existing_events: list[dict], new_events: list[dict]) -> list[dict]:
    merged = list(existing_events)
    seen = {item.get("event_id") for item in merged}
    for event in new_events:
        if event.get("event_id") in seen:
            continue
        merged.append(event)
        seen.add(event.get("event_id"))
    merged.sort(key=lambda item: (str(item.get("timestamp")), str(item.get("event_id"))))
    return merged


def _event_id(change_id: str, event_type: str, suffix: str | None) -> str:
    if suffix:
        return f"{change_id}-{event_type}-{suffix}"
    return f"{change_id}-{event_type}"


def _next_instance_event_id(
    existing_events: list[dict],
    *,
    change_id: str,
    event_type: str,
    event_suffix: str | None,
) -> str:
    base_id = _event_id(change_id, event_type, event_suffix)
    matching = [
        item.get("event_id", "")
        for item in existing_events
        if str(item.get("event_id", "")).startswith(base_id)
    ]
    return f"{base_id}-{len(matching) + 1:04d}"


def _event_timestamp(source_path: Path) -> str:
    if source_path.exists():
        return datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc).isoformat()
    return _now_utc()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
