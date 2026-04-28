from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def run_generic_file_command(request: dict) -> dict:
    if request.get("adapter_type") != "generic-file-command":
        raise ValueError("unsupported adapter_type")
    started_at = datetime.now(timezone.utc).isoformat()
    ended_at = datetime.now(timezone.utc).isoformat()
    return {
        "schema": "adapter-output/v1",
        "change_id": request.get("change_id"),
        "step": request.get("step", 6),
        "runtime_id": request.get("runtime_id", "generic-local-command"),
        "authority": request.get("authority", "evidence_input"),
        "status": request.get("status", "success"),
        "execution_status": request.get("status", "success"),
        "run_id": request.get("run_id", f"run-{uuid4().hex[:8]}"),
        "started_at": started_at,
        "completed_at": ended_at,
        "ended_at": ended_at,
        "adapter_type": "generic-file-command",
        "contract_path": request["contract_path"],
        "evidence_target": request.get("evidence_target"),
        "working_directory": request["working_directory"],
        "allowed_write_scope": request.get("allowed_write_scope", []),
        "timeout_seconds": request.get("timeout_seconds"),
        "command": request.get("command"),
        "commands": [request.get("command")] if request.get("command") else [],
        "command_output": request.get("command_output", ""),
        "test_output": request.get("test_output", ""),
        "artifacts": {
            "created": list(request.get("artifacts", {}).get("created", [])),
            "modified": list(request.get("artifacts", {}).get("modified", [])),
        },
        "verification": {
            "summary": request.get("test_output", ""),
            "status": "not-run" if not request.get("test_output") else "recorded",
        },
        "risks": list(request.get("risks", [])),
        "next_actions": list(request.get("next_actions", [])),
        "evidence_refs": list(request.get("evidence_refs", [])),
    }
