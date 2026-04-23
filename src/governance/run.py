from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from fnmatch import fnmatch

from adapters.generic_file_command import run_generic_file_command

from .contract import load_contract
from .evidence import ensure_required_evidence, write_evidence_bundle
from .paths import GovernancePaths


@dataclass
class AdapterRequest:
    change_id: str
    contract_path: str
    working_directory: str
    allowed_write_scope: list[str]
    timeout_seconds: int
    adapter_type: str = "generic-file-command"
    command: str | None = None
    command_output: str = ""
    test_output: str = ""
    artifacts: dict = field(default_factory=lambda: {"created": [], "modified": []})
    evidence_refs: list[str] = field(default_factory=list)
    status: str = "success"


@dataclass
class AdapterResponse:
    status: str
    run_id: str
    artifacts: dict
    evidence_refs: list[str]
    completed: bool


def run_change(root: str | Path, request: AdapterRequest) -> AdapterResponse:
    paths = GovernancePaths(Path(root))
    manifest_path = paths.change_file(request.change_id, "manifest.yaml")
    if manifest_path.exists():
        from .simple_yaml import load_yaml
        manifest = load_yaml(manifest_path)
        readiness = manifest.get("readiness", {})
        if not readiness.get("step6_entry_ready"):
            raise ValueError(f"change '{request.change_id}' is not ready for Step 6 execution (step6_entry_ready is not True)")

        bindings_path = paths.change_file(request.change_id, "bindings.yaml")
        if bindings_path.exists():
            bindings = load_yaml(bindings_path)
            from .state_consistency import _step_owner
            execution_owner = _step_owner(bindings, manifest, 6)
            verification_owner = _step_owner(bindings, manifest, 7)
            review_owner = _step_owner(bindings, manifest, 8)
            if execution_owner and verification_owner and execution_owner == verification_owner:
                raise ValueError(f"execution owner cannot be the same as verification owner for change '{request.change_id}'")
            if execution_owner and review_owner and execution_owner == review_owner:
                raise ValueError(f"execution owner cannot be the same as review owner for change '{request.change_id}'")

    contract = load_contract(request.contract_path)
    forbidden_actions = contract.get("forbidden_actions", [])
    if "no_executor_stable_write_authority" in forbidden_actions:
        for scope in request.allowed_write_scope:
            if ".governance/index" in scope or "current/" in scope:
                raise ValueError(f"executor does not have stable write authority for truth-source '{scope}'")
    _ensure_artifacts_within_write_boundary(request.artifacts, request.allowed_write_scope, contract.get("scope_out", []))
    _ensure_governance_reserved_boundaries(request.change_id, request.artifacts)

    response = run_generic_file_command(request.__dict__)
    evidence_dir = GovernancePaths(Path(root)).evidence_dir(request.change_id)
    written = write_evidence_bundle(evidence_dir, response)
    ensure_required_evidence(list(contract["evidence_expectations"]["required"]), written, list(response.get("evidence_refs", [])))
    evidence_refs = response["evidence_refs"] + sorted(str(Path(path).relative_to(evidence_dir.parent)) for path in written.values())
    return AdapterResponse(
        status=response["status"],
        run_id=response["run_id"],
        artifacts=response["artifacts"],
        evidence_refs=evidence_refs,
        completed=response["status"] == "success",
    )


def _ensure_artifacts_within_write_boundary(artifacts: dict, allowed_scopes: list[str], scope_out: list[str]) -> None:
    touched_paths = list(artifacts.get("created", [])) + list(artifacts.get("modified", []))
    for path in touched_paths:
        normalized = _normalize_artifact_path(path)
        if not any(fnmatch(normalized, pattern) for pattern in allowed_scopes):
            raise ValueError(f"artifact '{normalized}' is outside the allowed write boundary")
        if any(fnmatch(normalized, pattern) for pattern in scope_out):
            raise ValueError(f"artifact '{normalized}' is outside the allowed write boundary")


def _ensure_governance_reserved_boundaries(change_id: str, artifacts: dict) -> None:
    touched_paths = list(artifacts.get("created", [])) + list(artifacts.get("modified", []))
    for path in touched_paths:
        normalized = _normalize_artifact_path(path)
        if _is_reserved_governance_artifact(normalized):
            raise ValueError(f"artifact '{normalized}' touches a reserved governance boundary")


def _is_reserved_governance_artifact(path: str) -> bool:
    if path.startswith(".governance/index/"):
        return True
    if path.startswith(".governance/runtime/"):
        return True
    if path.startswith(".governance/archive/"):
        return True
    if path.startswith(".governance/changes/"):
        return True
    return False


def _normalize_artifact_path(path: str) -> str:
    normalized = str(Path(path)).replace("\\", "/")
    if normalized.startswith("/"):
        raise ValueError(f"artifact path '{path}' must be relative to the working directory")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError(f"artifact path '{path}' must remain within the working directory")
    return "/".join(parts)
