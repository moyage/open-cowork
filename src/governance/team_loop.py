from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .change_package import create_change_package
from .index import ensure_governance_index, read_active_changes, upsert_change_entry
from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml
from .step_matrix import STEP_LABELS, render_status_snapshot


TEAM_SCHEMA = "team-operating-loop/v1"


def team_status(root: str | Path) -> dict:
    paths = _paths(root)
    active = _active_change_summaries(paths)
    payload = {
        "schema": TEAM_SCHEMA,
        "generated_at": _now_utc(),
        "active_changes": active,
        "assignments": _read_team_file(paths, "assignments.yaml", {"assignments": []}).get("assignments", []),
        "blocked": _active_blocks(paths),
        "reviewer_queue": _reviewer_queue(paths),
        "recurring_intents": _read_team_file(paths, "recurring-intents.yaml", {"intents": []}).get("intents", []),
        "carry_forward": _read_team_file(paths, "carry-forward.yaml", {"items": []}).get("items", []),
        "retrospectives": _list_retrospectives(paths),
    }
    _write_team_file(paths, "operating-loop.yaml", payload)
    return payload


def format_team_status(payload: dict) -> str:
    lines = ["# Team operating loop", "", "## Active changes"]
    if payload["active_changes"]:
        for item in payload["active_changes"]:
            lines.append(
                f"- {item['change_id']}: step={item.get('current_step')} "
                f"status={item.get('status')} owner={item.get('owner') or 'unassigned'} "
                f"waiting_on={item.get('waiting_on')}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Blocked"])
    _append_short_items(lines, payload["blocked"], "id", ["change_id", "reason", "waiting_on"])
    lines.extend(["", "## Reviewer queue"])
    _append_short_items(lines, payload["reviewer_queue"], "change_id", ["reviewer", "priority", "independence"])
    lines.extend(["", "## Carry-forward"])
    _append_short_items(lines, payload["carry_forward"], "id", ["summary", "status", "source_change_id"])
    lines.extend(["", "## Retrospectives"])
    _append_short_items(lines, payload["retrospectives"], "id", ["change_id", "summary"])
    return "\n".join(lines) + "\n"


def team_digest(root: str | Path, *, period: str = "daily") -> dict:
    status = team_status(root)
    payload = {
        "schema": "team-digest/v1",
        "period": period,
        "generated_at": _now_utc(),
        "active_changes": status["active_changes"],
        "blocked": status["blocked"],
        "waiting_decisions": [
            {
                "change_id": item["change_id"],
                "next_decision": item.get("next_decision"),
                "waiting_on": item.get("waiting_on"),
            }
            for item in status["active_changes"]
            if item.get("next_decision") or item.get("waiting_on")
        ],
        "reviewer_queue": status["reviewer_queue"],
        "recent_verification_review_archive": _recent_verification_review_archive(_paths(root)),
        "carry_forward": status["carry_forward"],
        "retrospectives": status["retrospectives"],
    }
    _write_team_file(_paths(root), f"digest-{period}.yaml", payload)
    return payload


def format_team_digest(payload: dict) -> str:
    lines = [f"# Team digest ({payload['period']})", "", "## Waiting decisions"]
    _append_short_items(lines, payload["waiting_decisions"], "change_id", ["next_decision", "waiting_on"])
    lines.extend(["", "## Blocked"])
    _append_short_items(lines, payload["blocked"], "id", ["change_id", "reason", "waiting_on"])
    lines.extend(["", "## Reviewer queue"])
    _append_short_items(lines, payload["reviewer_queue"], "change_id", ["reviewer", "priority", "independence"])
    lines.extend(["", "## Carry-forward"])
    _append_short_items(lines, payload["carry_forward"], "id", ["summary", "status"])
    lines.extend(["", "## Retrospectives"])
    _append_short_items(lines, payload["retrospectives"], "id", ["change_id", "summary"])
    return "\n".join(lines) + "\n"


def participant_discover(root: str | Path, *, recorded_by: str = "agent") -> dict:
    paths = _paths(root)
    candidates = []
    for agent_id, command, domain, roles in [
        ("hermes", "hermes", "personal-local", ["executor", "reviewer", "analyst"]),
        ("omoc", "omoc", "personal-local", ["executor", "architect", "reviewer"]),
        ("opencode", "opencode", "personal-local", ["executor"]),
        ("codex", "codex", "personal-local", ["orchestrator", "executor"]),
    ]:
        executable = shutil.which(command)
        candidates.append({
            "id": agent_id,
            "type": "agent",
            "domain": domain,
            "entrypoint": executable or command,
            "available": bool(executable),
            "default_roles": roles,
            "human_confirmed": False,
            "discovered_at": _now_utc(),
        })
    payload = _participants_payload(paths)
    payload["discovered_candidates"] = candidates
    payload.setdefault("events", []).append(_event("discover", recorded_by, {"count": len(candidates)}))
    _write_team_file(paths, "participants.yaml", payload)
    _write_participant_event(paths, "discover", recorded_by, {"candidates": candidates})
    return payload


def participant_register(
    root: str | Path,
    *,
    participant_id: str,
    participant_type: str,
    domain: str,
    entrypoint: str,
    capability: list[str],
    default_role: list[str],
    step: list[int],
    recorded_by: str,
    remote: bool = False,
) -> dict:
    paths = _paths(root)
    payload = _participants_payload(paths)
    participants = payload.setdefault("participants", [])
    item = {
        "id": participant_id,
        "type": participant_type,
        "domain": domain,
        "entrypoint": entrypoint,
        "capabilities": list(capability or []),
        "default_roles": list(default_role or []),
        "eligible_steps": list(step or []),
        "remote": bool(remote),
        "human_confirmed": _is_human_actor(recorded_by),
        "review_status": "human-confirmed" if _is_human_actor(recorded_by) else "pending-human-review",
        "updated_at": _now_utc(),
    }
    if _is_human_actor(recorded_by):
        item["confirmed_by"] = recorded_by
    _upsert_by_id(participants, item)
    payload.setdefault("events", []).append(_event("register", recorded_by, {"participant_id": participant_id}))
    _write_team_file(paths, "participants.yaml", payload)
    _write_participant_event(paths, "register", recorded_by, item)
    return payload


def participant_update(root: str | Path, *, participant_id: str, updates: dict, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = _participants_payload(paths)
    participants = payload.setdefault("participants", [])
    for item in participants:
        if item.get("id") == participant_id:
            for key, value in updates.items():
                if value not in (None, [], ""):
                    item[key] = value
            item["updated_at"] = _now_utc()
            payload.setdefault("events", []).append(_event("update", recorded_by, {"participant_id": participant_id}))
            _write_team_file(paths, "participants.yaml", payload)
            _write_participant_event(paths, "update", recorded_by, item)
            return payload
    raise ValueError(f"participant not found: {participant_id}")


def participant_list(root: str | Path) -> dict:
    return _participants_payload(_paths(root))


def assignment_set(
    root: str | Path,
    *,
    change_id: str,
    step: int,
    role: str,
    actor: str,
    recorded_by: str,
    note: str = "",
) -> dict:
    if step < 1 or step > 9:
        raise ValueError("step must be 1..9")
    if role not in {"owner", "executor", "reviewer", "participant"}:
        raise ValueError("role must be owner, executor, reviewer, or participant")
    paths = _paths(root)
    payload = _read_team_file(paths, "assignments.yaml", {"schema": "team-assignments/v1", "assignments": [], "events": []})
    assignments = payload.setdefault("assignments", [])
    if role == "reviewer":
        executor = (
            _assigned_actor(assignments, change_id, step, "executor")
            or _assigned_actor(assignments, change_id, 6, "executor")
            or _binding_actor(paths, change_id, 6, "executor")
            or _binding_actor(paths, change_id, 6, "owner")
        )
        if executor and executor == actor:
            raise ValueError("reviewer cannot review their own execution")
    item = {
        "change_id": change_id,
        "step": step,
        "step_label": STEP_LABELS.get(step),
        "role": role,
        "actor": actor,
        "note": note,
        "updated_at": _now_utc(),
        "recorded_by": recorded_by,
    }
    _upsert_assignment(assignments, item)
    payload.setdefault("events", []).append(_event("assignment_set", recorded_by, item))
    _write_team_file(paths, "assignments.yaml", payload)
    _sync_change_bindings(paths, change_id, step, role, actor)
    return payload


def participant_assign(root: str | Path, **kwargs) -> dict:
    payload = assignment_set(root, **kwargs)
    paths = _paths(root)
    participants = _participants_payload(paths)
    participants.setdefault("events", []).append(_event("assign", kwargs.get("recorded_by", "agent"), kwargs))
    _write_team_file(paths, "participants.yaml", participants)
    _write_participant_event(paths, "assign", kwargs.get("recorded_by", "agent"), kwargs)
    return payload


def blocked_set(root: str | Path, *, change_id: str, reason: str, waiting_on: str, next_decision: str, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "blocked.yaml", {"schema": "team-blocked/v1", "blocks": [], "history": []})
    block_id = _slug(f"{change_id}-{reason}")[:80]
    block = {
        "id": block_id,
        "change_id": change_id,
        "reason": reason,
        "waiting_on": waiting_on,
        "next_decision": next_decision,
        "status": "active",
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
    }
    _upsert_by_id(payload.setdefault("blocks", []), block)
    payload.setdefault("history", []).append(_event("blocked_set", recorded_by, block))
    _write_team_file(paths, "blocked.yaml", payload)
    return payload


def blocked_clear(root: str | Path, *, block_id: str, recorded_by: str, resolution: str = "") -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "blocked.yaml", {"schema": "team-blocked/v1", "blocks": [], "history": []})
    found = False
    for block in payload.setdefault("blocks", []):
        if block.get("id") == block_id:
            block["status"] = "cleared"
            block["cleared_by"] = recorded_by
            block["cleared_at"] = _now_utc()
            block["resolution"] = resolution
            found = True
    if not found:
        raise ValueError(f"block not found: {block_id}")
    payload.setdefault("history", []).append(_event("blocked_clear", recorded_by, {"id": block_id, "resolution": resolution}))
    _write_team_file(paths, "blocked.yaml", payload)
    return payload


def reviewer_queue(root: str | Path, *, change_id: str | None = None, reviewer: str = "", priority: str = "normal", recorded_by: str = "") -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "reviewer-queue.yaml", {"schema": "team-reviewer-queue/v1", "queue": [], "events": []})
    if change_id:
        independence = _reviewer_independence(paths, change_id, reviewer)
        item = {
            "change_id": change_id,
            "reviewer": reviewer,
            "priority": priority,
            "independence": independence,
            "status": "queued",
            "recorded_by": recorded_by,
            "queued_at": _now_utc(),
        }
        _upsert_queue(payload.setdefault("queue", []), item)
        payload.setdefault("events", []).append(_event("reviewer_queue", recorded_by, item))
        _write_team_file(paths, "reviewer-queue.yaml", payload)
    return payload


def recurring_intent_add(root: str | Path, *, intent_id: str, summary: str, cadence: str, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "recurring-intents.yaml", {"schema": "team-recurring-intents/v1", "intents": [], "events": []})
    item = {
        "id": intent_id,
        "summary": summary,
        "cadence": cadence,
        "status": "active",
        "recorded_by": recorded_by,
        "updated_at": _now_utc(),
    }
    _upsert_by_id(payload.setdefault("intents", []), item)
    payload.setdefault("events", []).append(_event("recurring_intent_add", recorded_by, item))
    _write_team_file(paths, "recurring-intents.yaml", payload)
    return payload


def recurring_intent_trigger(root: str | Path, *, intent_id: str, change_id: str, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "recurring-intents.yaml", {"schema": "team-recurring-intents/v1", "intents": [], "events": []})
    intent = next((item for item in payload.get("intents", []) if item.get("id") == intent_id), None)
    if not intent:
        raise ValueError(f"recurring intent not found: {intent_id}")
    package = create_change_package(paths.root, change_id, title=intent.get("summary") or change_id)
    manifest = dict(package.manifest)
    manifest.update({"status": "awaiting-intent-confirmation", "current_step": 1, "triggered_by_recurring_intent": intent_id})
    write_yaml(package.path / "manifest.yaml", manifest)
    write_yaml(package.path / "intent-confirmation.yaml", {
        "schema": "intent-confirmation/v1",
        "change_id": change_id,
        "status": "pending-human-confirmation",
        "project_intent": intent.get("summary"),
        "human_confirmation": {"status": "pending"},
        "captured_at": _now_utc(),
    })
    ensure_governance_index(paths.root)
    upsert_change_entry(paths.root, {
        "change_id": change_id,
        "path": str(package.path.relative_to(paths.root)),
        "status": manifest["status"],
        "current_step": 1,
        "title": manifest.get("title"),
    })
    event = _event("recurring_intent_trigger", recorded_by, {"intent_id": intent_id, "change_id": change_id})
    payload.setdefault("events", []).append(event)
    intent["last_triggered_change_id"] = change_id
    intent["last_triggered_at"] = event["recorded_at"]
    _write_team_file(paths, "recurring-intents.yaml", payload)
    return {"schema": "recurring-intent-trigger/v1", "intent_id": intent_id, "change_id": change_id, "status": manifest["status"], "current_step": 1}


def carry_forward_add(root: str | Path, *, item_id: str, summary: str, source_change_id: str, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = _read_team_file(paths, "carry-forward.yaml", {"schema": "team-carry-forward/v1", "items": [], "events": []})
    item = {
        "id": item_id,
        "summary": summary,
        "source_change_id": source_change_id,
        "status": "candidate",
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
    }
    _upsert_by_id(payload.setdefault("items", []), item)
    payload.setdefault("events", []).append(_event("carry_forward_add", recorded_by, item))
    _write_team_file(paths, "carry-forward.yaml", payload)
    return payload


def carry_forward_list(root: str | Path) -> dict:
    return _read_team_file(_paths(root), "carry-forward.yaml", {"schema": "team-carry-forward/v1", "items": [], "events": []})


def carry_forward_promote(root: str | Path, *, item_id: str, change_id: str, recorded_by: str) -> dict:
    paths = _paths(root)
    payload = carry_forward_list(root)
    item = next((entry for entry in payload.get("items", []) if entry.get("id") == item_id), None)
    if not item:
        raise ValueError(f"carry-forward item not found: {item_id}")
    package = create_change_package(paths.root, change_id, title=item.get("summary") or change_id)
    manifest = dict(package.manifest)
    manifest.update({"status": "awaiting-intent-confirmation", "current_step": 1, "promoted_from_carry_forward": item_id})
    write_yaml(package.path / "manifest.yaml", manifest)
    item["status"] = "promoted"
    item["promoted_change_id"] = change_id
    item["promoted_at"] = _now_utc()
    item["promoted_by"] = recorded_by
    payload.setdefault("events", []).append(_event("carry_forward_promote", recorded_by, {"item_id": item_id, "change_id": change_id}))
    _write_team_file(paths, "carry-forward.yaml", payload)
    ensure_governance_index(paths.root)
    upsert_change_entry(paths.root, {
        "change_id": change_id,
        "path": str(package.path.relative_to(paths.root)),
        "status": manifest["status"],
        "current_step": 1,
        "title": manifest.get("title"),
    })
    return payload


def retrospective_add(root: str | Path, *, retrospective_id: str, change_id: str, summary: str, learning: list[str], recorded_by: str) -> dict:
    paths = _paths(root)
    directory = _team_dir(paths) / "retrospectives"
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "team-retrospective/v1",
        "id": retrospective_id,
        "change_id": change_id,
        "summary": summary,
        "learning": list(learning or []),
        "recorded_by": recorded_by,
        "recorded_at": _now_utc(),
    }
    write_yaml(directory / f"{retrospective_id}.yaml", payload)
    (directory / f"{retrospective_id}.md").write_text(format_retrospective(payload), encoding="utf-8")
    return payload


def retrospective_list(root: str | Path) -> dict:
    return {"schema": "team-retrospectives/v1", "retrospectives": _list_retrospectives(_paths(root))}


def format_retrospective(payload: dict) -> str:
    lines = [f"# Retrospective: {payload['id']}", "", f"- change_id: {payload['change_id']}", f"- summary: {payload['summary']}", "", "## Learnings"]
    for item in payload.get("learning", []):
        lines.append(f"- {item}")
    if not payload.get("learning"):
        lines.append("- none")
    return "\n".join(lines) + "\n"


def format_item_list(title: str, items: list[dict], id_key: str = "id") -> str:
    lines = [f"# {title}", ""]
    _append_short_items(lines, items, id_key, [])
    return "\n".join(lines) + "\n"


def _active_change_summaries(paths: GovernancePaths) -> list[dict]:
    ensure_governance_index(paths.root)
    active = read_active_changes(paths.root).get("changes", [])
    assignments = _read_team_file(paths, "assignments.yaml", {"assignments": []}).get("assignments", [])
    blocks = _active_blocks(paths)
    summaries = []
    for entry in active:
        change_id = entry.get("change_id")
        if not change_id:
            continue
        try:
            snapshot = render_status_snapshot(paths.root, change_id)
        except Exception:
            snapshot = {}
        summaries.append({
            "change_id": change_id,
            "status": entry.get("status"),
            "current_step": entry.get("current_step"),
            "title": entry.get("title"),
            "owner": _assignment_for(assignments, change_id, "owner") or entry.get("owner") or snapshot.get("current_owner"),
            "executor": _assignment_for(assignments, change_id, "executor"),
            "reviewer": _assignment_for(assignments, change_id, "reviewer"),
            "waiting_on": _block_waiting_on(blocks, change_id) or snapshot.get("waiting_on"),
            "next_decision": snapshot.get("next_decision"),
            "recent_evidence": _relative_if_exists(paths, paths.change_dir(change_id) / "evidence"),
            "verify_status": _file_status(paths.change_file(change_id, "verify.yaml")),
            "review_status": _review_status(paths.change_file(change_id, "review.yaml")),
            "near_archive": entry.get("current_step") in {8, 9} or entry.get("status") in {"review-approved"},
        })
    return summaries


def _recent_verification_review_archive(paths: GovernancePaths) -> dict:
    return {
        "archive_map_ref": str(paths.archive_map_file().relative_to(paths.root)) if paths.archive_map_file().exists() else None,
        "maintenance_status_ref": str(paths.maintenance_status_file().relative_to(paths.root)) if paths.maintenance_status_file().exists() else None,
    }


def _paths(root: str | Path) -> GovernancePaths:
    return GovernancePaths(Path(root))


def _team_dir(paths: GovernancePaths) -> Path:
    directory = paths.governance_dir / "team"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _read_team_file(paths: GovernancePaths, name: str, default: dict) -> dict:
    path = _team_dir(paths) / name
    if not path.exists():
        return dict(default)
    return load_yaml(path)


def _write_team_file(paths: GovernancePaths, name: str, payload: dict) -> None:
    path = _team_dir(paths) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(path, payload)


def _participants_payload(paths: GovernancePaths) -> dict:
    return _read_team_file(paths, "participants.yaml", {"schema": "team-participants/v1", "participants": [], "discovered_candidates": [], "events": []})


def _write_participant_event(paths: GovernancePaths, action: str, recorded_by: str, payload: dict) -> None:
    directory = _team_dir(paths) / "participant-events"
    directory.mkdir(parents=True, exist_ok=True)
    write_yaml(directory / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-{action}.yaml", _event(action, recorded_by, payload))


def _event(action: str, recorded_by: str, payload: dict) -> dict:
    return {"action": action, "recorded_by": recorded_by, "recorded_at": _now_utc(), "payload": payload}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_by_id(items: list[dict], new_item: dict) -> None:
    for index, item in enumerate(items):
        if item.get("id") == new_item.get("id"):
            items[index] = {**item, **new_item}
            return
    items.append(new_item)


def _upsert_assignment(items: list[dict], new_item: dict) -> None:
    for index, item in enumerate(items):
        if item.get("change_id") == new_item.get("change_id") and item.get("step") == new_item.get("step") and item.get("role") == new_item.get("role"):
            items[index] = {**item, **new_item}
            return
    items.append(new_item)


def _upsert_queue(items: list[dict], new_item: dict) -> None:
    for index, item in enumerate(items):
        if item.get("change_id") == new_item.get("change_id"):
            items[index] = {**item, **new_item}
            return
    items.append(new_item)


def _assigned_actor(assignments: list[dict], change_id: str, step: int, role: str) -> str | None:
    for item in reversed(assignments):
        if item.get("change_id") == change_id and item.get("step") == step and item.get("role") == role:
            return item.get("actor")
    return None


def _assignment_for(assignments: list[dict], change_id: str, role: str) -> str | None:
    for item in reversed(assignments):
        if item.get("change_id") == change_id and item.get("role") == role:
            return item.get("actor")
    return None


def _sync_change_bindings(paths: GovernancePaths, change_id: str, step: int, role: str, actor: str) -> None:
    path = paths.change_file(change_id, "bindings.yaml")
    if not path.exists():
        return
    bindings = load_yaml(path)
    steps = bindings.setdefault("steps", {})
    step_payload = steps.setdefault(str(step), {})
    if role == "owner":
        step_payload["owner"] = actor
    elif role == "reviewer":
        step_payload["reviewer"] = actor
    elif role == "participant":
        assistants = list(step_payload.get("assistants") or [])
        if actor not in assistants:
            assistants.append(actor)
        step_payload["assistants"] = assistants
    elif role == "executor":
        step_payload["executor"] = actor
        if step == 6:
            step_payload["owner"] = actor
    write_yaml(path, bindings)


def _reviewer_independence(paths: GovernancePaths, change_id: str, reviewer: str) -> str:
    assignments = _read_team_file(paths, "assignments.yaml", {"assignments": []}).get("assignments", [])
    executor = _assignment_for(assignments, change_id, "executor") or _binding_actor(paths, change_id, 6, "executor") or _binding_actor(paths, change_id, 6, "owner")
    if executor and reviewer and executor == reviewer:
        return "blocked_self_review"
    return "independent" if reviewer else "unassigned"


def _binding_actor(paths: GovernancePaths, change_id: str, step: int, role: str) -> str | None:
    path = paths.change_file(change_id, "bindings.yaml")
    if not path.exists():
        return None
    bindings = load_yaml(path)
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    step_payload = steps.get(step) or steps.get(str(step)) or steps.get(f"'{step}'") or {}
    if isinstance(step_payload, dict):
        return step_payload.get(role)
    return None


def _is_human_actor(actor: str) -> bool:
    normalized = (actor or "").strip().lower()
    return normalized.startswith("human") or normalized.endswith("-human") or normalized in {"sponsor", "maintainer-human"}


def _active_blocks(paths: GovernancePaths) -> list[dict]:
    blocks = _read_team_file(paths, "blocked.yaml", {"blocks": []}).get("blocks", [])
    return [item for item in blocks if item.get("status") != "cleared"]


def _reviewer_queue(paths: GovernancePaths) -> list[dict]:
    return _read_team_file(paths, "reviewer-queue.yaml", {"queue": []}).get("queue", [])


def _block_waiting_on(blocks: list[dict], change_id: str) -> str | None:
    for block in blocks:
        if block.get("change_id") == change_id:
            return block.get("waiting_on")
    return None


def _file_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    payload = load_yaml(path)
    return payload.get("status") or payload.get("verification", {}).get("status") or "present"


def _review_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    payload = load_yaml(path)
    return payload.get("decision", {}).get("status") or payload.get("status") or "present"


def _relative_if_exists(paths: GovernancePaths, path: Path) -> str | None:
    return str(path.relative_to(paths.root)) if path.exists() else None


def _list_retrospectives(paths: GovernancePaths) -> list[dict]:
    directory = _team_dir(paths) / "retrospectives"
    if not directory.exists():
        return []
    items = []
    for path in sorted(directory.glob("*.yaml")):
        payload = load_yaml(path)
        items.append({
            "id": payload.get("id") or path.stem,
            "change_id": payload.get("change_id"),
            "summary": payload.get("summary"),
            "ref": str(path.relative_to(paths.root)),
        })
    return items


def _append_short_items(lines: list[str], items: list[dict], id_key: str, fields: list[str]) -> None:
    if not items:
        lines.append("- none")
        return
    for item in items:
        parts = [str(item.get(id_key) or item.get("change_id") or item.get("id"))]
        for field in fields:
            if item.get(field) not in (None, "", []):
                parts.append(f"{field}={item.get(field)}")
        if not fields:
            for key, value in item.items():
                if key not in {"events", "payload"} and value not in (None, "", []):
                    parts.append(f"{key}={value}")
        lines.append("- " + " ".join(parts))


def _slug(value: str) -> str:
    chars = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "item"
