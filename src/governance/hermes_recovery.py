from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .paths import GovernancePaths
from .simple_yaml import load_yaml, write_yaml

HERMES_RECOVERY_SCHEMA = "governance/session-recovery-diagnosis/v1"
DEFAULT_CONTEXT_BUDGET_TOKENS = 12000
DEFAULT_RECOVERY_PACKET_NAME = "SESSION_RECOVERY_PACKET.yaml"


def diagnose_hermes_execution_stall(
    root: str | Path,
    context_budget_tokens: int = DEFAULT_CONTEXT_BUDGET_TOKENS,
    change_id: str | None = None,
    session_log_path: str | Path | None = None,
) -> dict:
    paths = GovernancePaths(Path(root))
    current_change = load_yaml(paths.current_change_file()) if paths.current_change_file().exists() else {}
    maintenance = load_yaml(paths.maintenance_status_file()) if paths.maintenance_status_file().exists() else {}
    archive_map = load_yaml(paths.archive_map_file()) if paths.archive_map_file().exists() else {}

    active_change_id = _extract_current_change_id(current_change)
    target_change_id = str(change_id or active_change_id or maintenance.get("last_archived_change") or "")
    lifecycle_phase = _resolve_lifecycle_phase(current_change, maintenance, target_change_id, active_change_id)

    duplicate_surface = _detect_duplicate_surface(paths, target_change_id) if target_change_id else _empty_duplicate_surface()
    recommended_read_set = _recommended_read_set(paths, lifecycle_phase, target_change_id, active_change_id)
    full_scan_estimate = _estimate_scan_tokens(_default_full_scan_files(paths))
    recommended_estimate = _estimate_scan_tokens([paths.root / item["path"] for item in recommended_read_set])
    runtime_failure = _diagnose_runtime_failure(session_log_path)

    root_causes = []
    if lifecycle_phase == "idle_post_close":
        root_causes.append({
            "id": "RC1_CLOSE_REENTRY_ON_IDLE",
            "summary": "Round close was re-entered after archive completion while lifecycle is already idle.",
            "evidence": {
                "current_change_id": active_change_id,
                "maintenance_status": maintenance.get("status"),
                "last_archived_change": maintenance.get("last_archived_change"),
            },
        })
    if duplicate_surface["identical_count"] > 0:
        root_causes.append({
            "id": "RC2_DUPLICATE_READ_SURFACE",
            "summary": "The same artifacts exist in both active and archive paths, which can double context with no additional signal.",
            "evidence": {
                "change_id": target_change_id,
                "identical_count": duplicate_surface["identical_count"],
                "identical_bytes": duplicate_surface["identical_bytes"],
            },
        })
    if full_scan_estimate["estimated_tokens"] > int(context_budget_tokens):
        root_causes.append({
            "id": "RC3_CONTEXT_BUDGET_EXCEEDED",
            "summary": "Unbounded full scan exceeds the context budget and is likely to trigger repeated compression or provider drop.",
            "evidence": {
                "budget_tokens": int(context_budget_tokens),
                "full_scan_estimated_tokens": full_scan_estimate["estimated_tokens"],
            },
        })
    if runtime_failure.get("status") == "remote_compact_stream_disconnected":
        root_causes.append({
            "id": "RC4_REMOTE_COMPACT_STREAM_DISCONNECTED",
            "summary": "Codex remote context compact request disconnected before completion, leaving no final agent message.",
            "evidence": {
                "session_log": runtime_failure.get("session_log"),
                "last_error_at": runtime_failure.get("last_error_at"),
                "message": runtime_failure.get("last_error_message"),
                "last_token_count": runtime_failure.get("last_token_count"),
                "task_completed_without_agent_message": runtime_failure.get("task_completed_without_agent_message"),
            },
        })
    if not root_causes:
        root_causes.append({
            "id": "RC0_NO_HARD_BLOCKER_FOUND",
            "summary": "No deterministic local blocker was detected; prioritize provider-side telemetry and retry strategy.",
            "evidence": {"target_change_id": target_change_id or None},
        })

    archive_entry = _find_archive_entry(archive_map, target_change_id) if target_change_id else {}
    return {
        "schema": HERMES_RECOVERY_SCHEMA,
        "target_change_id": target_change_id or None,
        "lifecycle_phase": lifecycle_phase,
        "root_causes": root_causes,
        "archive_context": {
            "last_archived_change": maintenance.get("last_archived_change"),
            "last_archive_at": maintenance.get("last_archive_at"),
            "archive_entry": archive_entry,
        },
        "duplicate_surface": duplicate_surface,
        "runtime_failure": runtime_failure,
        "context_budget": {
            "budget_tokens": int(context_budget_tokens),
            "full_scan_estimated_tokens": full_scan_estimate["estimated_tokens"],
            "recommended_set_estimated_tokens": recommended_estimate["estimated_tokens"],
            "full_scan_file_count": full_scan_estimate["file_count"],
            "recommended_file_count": recommended_estimate["file_count"],
        },
        "recommended_read_set": recommended_read_set,
        "recommended_execution_mode": _recommended_execution_mode(lifecycle_phase, target_change_id),
        "immediate_actions": _immediate_actions(lifecycle_phase, target_change_id),
    }


def materialize_hermes_recovery_packet(
    root: str | Path,
    context_budget_tokens: int = DEFAULT_CONTEXT_BUDGET_TOKENS,
    change_id: str | None = None,
    output_path: str | Path | None = None,
    session_log_path: str | Path | None = None,
) -> str:
    payload = diagnose_hermes_execution_stall(
        root,
        context_budget_tokens=context_budget_tokens,
        change_id=change_id,
        session_log_path=session_log_path,
    )
    paths = GovernancePaths(Path(root))
    target = Path(output_path) if output_path else paths.index_dir / DEFAULT_RECOVERY_PACKET_NAME
    write_yaml(target, payload)
    return str(target)


def _resolve_lifecycle_phase(current_change: dict, maintenance: dict, target_change_id: str, active_change_id: str | None) -> str:
    maintenance_status = str(maintenance.get("status") or "").lower()
    current_status = str(current_change.get("status") or "").lower()
    if not active_change_id and (
        "idle" in maintenance_status
        or "idle" in current_status
        or maintenance.get("current_change_active") in {"none", "inactive", False}
    ):
        if target_change_id and maintenance.get("last_archived_change"):
            return "idle_post_close"
        return "idle_no_archive"
    if active_change_id:
        if any(token in current_status for token in ("step8", "step9", "close")):
            return "active_close_window"
        return "active_change_window"
    return "unknown"


def _recommended_read_set(
    paths: GovernancePaths,
    lifecycle_phase: str,
    target_change_id: str,
    active_change_id: str | None,
) -> list[dict]:
    refs: list[dict] = [
        {"path": ".governance/index/maintenance-status.yaml", "role": "maintenance-status"},
        {"path": ".governance/index/current-change.yaml", "role": "current-change"},
    ]

    if lifecycle_phase == "idle_post_close" and target_change_id:
        refs.extend(_change_close_packet_refs(paths, target_change_id, archived=True))
        return _dedup_existing_refs(paths, refs)

    selected_change_id = active_change_id or target_change_id
    if selected_change_id:
        refs.extend(_change_launch_packet_refs(paths, selected_change_id))
    return _dedup_existing_refs(paths, refs)


def _change_close_packet_refs(paths: GovernancePaths, change_id: str, archived: bool) -> list[dict]:
    base = paths.archived_change_dir(change_id) if archived else paths.change_dir(change_id)
    rel_base = ".governance/archive" if archived else ".governance/changes"
    refs = []
    for name, role in [
        ("archive-receipt.yaml", "archive-receipt"),
        ("review.yaml", "review-decision"),
        ("verify.yaml", "verify-evidence"),
        ("STATE_CONSISTENCY_CHECK.yaml", "state-consistency"),
        ("STEP_MATRIX_VIEW.md", "step-matrix"),
        ("ROUND_ENTRY_INPUT_SUMMARY.yaml", "round-entry-summary"),
        ("manifest.yaml", "manifest"),
    ]:
        refs.append({"path": f"{rel_base}/{change_id}/{name}", "role": role})

    close_summaries = sorted(base.glob("ROUND*_CLOSE_OUT_SUMMARY.yaml"))
    for summary in close_summaries:
        refs.append({"path": str(summary.relative_to(paths.root)), "role": "round-close-summary"})
    return refs


def _change_launch_packet_refs(paths: GovernancePaths, change_id: str) -> list[dict]:
    refs = []
    for name, role in [
        ("manifest.yaml", "manifest"),
        ("contract.yaml", "contract"),
        ("requirements.md", "requirements"),
        ("tasks.md", "tasks"),
        ("bindings.yaml", "bindings"),
        ("ROUND_ENTRY_INPUT_SUMMARY.yaml", "round-entry-summary"),
    ]:
        refs.append({"path": f".governance/changes/{change_id}/{name}", "role": role})
    refs.append({"path": ".governance/index/changes-index.yaml", "role": "changes-index"})
    refs.append({"path": ".governance/index/archive-map.yaml", "role": "archive-map"})
    return refs


def _dedup_existing_refs(paths: GovernancePaths, refs: list[dict]) -> list[dict]:
    deduped = []
    seen: set[str] = set()
    for item in refs:
        path = str(item.get("path") or "")
        if not path or path in seen:
            continue
        full = paths.root / path
        if full.exists() and full.is_file():
            seen.add(path)
            deduped.append({"path": path, "role": item.get("role")})
    return deduped


def _detect_duplicate_surface(paths: GovernancePaths, change_id: str) -> dict:
    active = paths.change_dir(change_id)
    archived = paths.archived_change_dir(change_id)
    if not active.exists() or not archived.exists():
        return _empty_duplicate_surface()

    active_files = {
        str(p.relative_to(active)): p
        for p in active.rglob("*")
        if p.is_file() and _is_context_file(p)
    }
    archived_files = {
        str(p.relative_to(archived)): p
        for p in archived.rglob("*")
        if p.is_file() and _is_context_file(p)
    }
    common = sorted(set(active_files) & set(archived_files))
    identical = []
    different = []
    identical_bytes = 0
    for rel in common:
        left = active_files[rel]
        right = archived_files[rel]
        if _sha256(left) == _sha256(right):
            identical.append(rel)
            identical_bytes += left.stat().st_size
        else:
            different.append(rel)
    return {
        "active_file_count": len(active_files),
        "archive_file_count": len(archived_files),
        "paired_count": len(common),
        "identical_count": len(identical),
        "different_count": len(different),
        "identical_bytes": identical_bytes,
        "sample_identical_files": identical[:10],
        "sample_different_files": different[:10],
    }


def _default_full_scan_files(paths: GovernancePaths) -> list[Path]:
    patterns = [
        ".governance/**/*.md",
        ".governance/**/*.yaml",
        "docs/**/*.md",
        "src/**/*.py",
        "tests/**/*.py",
        "bin/*",
    ]
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for item in paths.root.glob(pattern):
            if item.is_file() and item not in seen:
                seen.add(item)
                files.append(item)
    return files


def _estimate_scan_tokens(files: list[Path]) -> dict:
    chars = 0
    words = 0
    counted_files = 0
    for file in files:
        if not file.exists() or not file.is_file():
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        counted_files += 1
        chars += len(text)
        words += len(re.findall(r"\w+", text))
    estimated_tokens = max(int(words * 1.3), int(chars / 3)) if counted_files else 0
    return {
        "file_count": counted_files,
        "chars": chars,
        "words": words,
        "estimated_tokens": estimated_tokens,
    }


def _diagnose_runtime_failure(session_log_path: str | Path | None) -> dict:
    if not session_log_path:
        return {"status": "not-provided"}
    path = Path(session_log_path)
    if not path.exists() or not path.is_file():
        return {"status": "session-log-missing", "session_log": str(path)}

    last_token_count: dict = {}
    last_error: dict = {}
    task_completed_without_agent_message = False
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload") if isinstance(event, dict) else {}
            if not isinstance(payload, dict):
                continue
            if payload.get("type") == "token_count":
                info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
                usage = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
                last_token_count = dict(usage)
                if "model_context_window" in info:
                    last_token_count["model_context_window"] = info.get("model_context_window")
            if payload.get("type") == "error":
                last_error = {
                    "timestamp": event.get("timestamp"),
                    "message": payload.get("message"),
                    "codex_error_info": payload.get("codex_error_info"),
                }
            if payload.get("type") == "task_complete" and not payload.get("last_agent_message"):
                task_completed_without_agent_message = True
    except OSError as exc:
        return {"status": "session-log-unreadable", "session_log": str(path), "error": str(exc)}

    message = str(last_error.get("message") or "")
    if "Error running remote compact task" in message and "stream disconnected before completion" in message:
        return {
            "status": "remote_compact_stream_disconnected",
            "session_log": str(path),
            "last_error_at": last_error.get("timestamp"),
            "last_error_message": message,
            "codex_error_info": last_error.get("codex_error_info"),
            "last_token_count": last_token_count,
            "task_completed_without_agent_message": task_completed_without_agent_message,
        }
    if last_error:
        return {
            "status": "codex-runtime-error",
            "session_log": str(path),
            "last_error_at": last_error.get("timestamp"),
            "last_error_message": message,
            "codex_error_info": last_error.get("codex_error_info"),
            "last_token_count": last_token_count,
            "task_completed_without_agent_message": task_completed_without_agent_message,
        }
    return {
        "status": "no-runtime-error-detected",
        "session_log": str(path),
        "last_token_count": last_token_count,
        "task_completed_without_agent_message": task_completed_without_agent_message,
    }


def _recommended_execution_mode(lifecycle_phase: str, target_change_id: str) -> dict:
    if lifecycle_phase == "idle_post_close":
        return {
            "mode": "post-close-idle",
            "instruction": "Do not re-run close on archived round; create or activate next change package before execution.",
            "target_change_id": target_change_id or None,
        }
    if lifecycle_phase == "active_change_window":
        return {
            "mode": "active-change",
            "instruction": "Use round-entry compact packet and avoid scanning archived duplicate artifacts.",
            "target_change_id": target_change_id or None,
        }
    return {
        "mode": "diagnostic-only",
        "instruction": "Lifecycle state is unclear; prefer deterministic index status before dispatch.",
        "target_change_id": target_change_id or None,
    }


def _immediate_actions(lifecycle_phase: str, target_change_id: str) -> list[dict]:
    if lifecycle_phase == "idle_post_close":
        return [
            {
                "order": 1,
                "action": "start_new_change",
                "detail": "Create or set a new active change package instead of re-closing the archived round.",
            },
            {
                "order": 2,
                "action": "bound_context",
                "detail": "Load only recommended_read_set; never read both .governance/changes and .governance/archive for the same change.",
            },
            {
                "order": 3,
                "action": "resume_with_packet",
                "detail": "Resume Hermes with this diagnosis packet as the only mandatory context input.",
            },
        ]
    return [
        {
            "order": 1,
            "action": "bound_context",
            "detail": "Restrict context to recommended_read_set and keep total token budget bounded per run.",
        },
        {
            "order": 2,
            "action": "verify_stage",
            "detail": "Confirm current step and gate ownership before dispatching any execution adapter.",
        },
    ]


def _extract_current_change_id(payload: dict) -> str | None:
    nested = payload.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    return payload.get("current_change_id") or nested.get("change_id") or nested.get("current_change_id")


def _find_archive_entry(archive_map: dict, change_id: str) -> dict:
    for entry in archive_map.get("archives", []):
        if entry.get("change_id") == change_id:
            return entry
    return {}


def _empty_duplicate_surface() -> dict:
    return {
        "active_file_count": 0,
        "archive_file_count": 0,
        "paired_count": 0,
        "identical_count": 0,
        "different_count": 0,
        "identical_bytes": 0,
        "sample_identical_files": [],
        "sample_different_files": [],
    }


def _is_context_file(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".yaml", ".yml"}


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()
