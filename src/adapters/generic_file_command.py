from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def run_generic_file_command(request: dict) -> dict:
    if request.get("adapter_type") != "generic-file-command":
        raise ValueError("unsupported adapter_type")
    started_at = datetime.now(timezone.utc).isoformat()
    return {
        "status": request.get("status", "success"),
        "run_id": request.get("run_id", f"run-{uuid4().hex[:8]}"),
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "adapter_type": "generic-file-command",
        "contract_path": request["contract_path"],
        "working_directory": request["working_directory"],
        "allowed_write_scope": request.get("allowed_write_scope", []),
        "timeout_seconds": request.get("timeout_seconds"),
        "command": request.get("command"),
        "command_output": request.get("command_output", ""),
        "test_output": request.get("test_output", ""),
        "artifacts": {
            "created": list(request.get("artifacts", {}).get("created", [])),
            "modified": list(request.get("artifacts", {}).get("modified", [])),
        },
        "evidence_refs": list(request.get("evidence_refs", [])),
    }
