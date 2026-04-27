from __future__ import annotations

from pathlib import Path

from .simple_yaml import write_yaml

EVIDENCE_FILES = {
    "execution_summary": "execution-summary.yaml",
    "changed_files_manifest": "changed-files-manifest.yaml",
    "command_output": "command-output-summary.yaml",
    "test_output": "test-output-summary.yaml",
    "file_diff": "file-diff-summary.yaml",
}


class MissingEvidenceError(ValueError):
    pass


def write_evidence_bundle(evidence_dir: str | Path, response: dict) -> dict:
    evidence_path = Path(evidence_dir)
    evidence_path.mkdir(parents=True, exist_ok=True)
    written = {
        "execution_summary": _write(evidence_path / EVIDENCE_FILES["execution_summary"], {
            "status": response["status"],
            "run_id": response["run_id"],
            "adapter_type": response.get("adapter_type"),
            "artifacts": response.get("artifacts", {}),
            "evidence_refs": response.get("evidence_refs", []),
        }),
        "changed_files_manifest": _write(evidence_path / EVIDENCE_FILES["changed_files_manifest"], {
            "created": response.get("artifacts", {}).get("created", []),
            "modified": response.get("artifacts", {}).get("modified", []),
        }),
        "command_output": _write(evidence_path / EVIDENCE_FILES["command_output"], {
            "command": response.get("command"),
            "summary": response.get("command_output", ""),
        }),
        "test_output": _write(evidence_path / EVIDENCE_FILES["test_output"], {
            "summary": response.get("test_output", ""),
        }),
        "file_diff": _write(evidence_path / EVIDENCE_FILES["file_diff"], {
            "changed_files": sorted(set(response.get("artifacts", {}).get("created", []) + response.get("artifacts", {}).get("modified", []))),
        }),
    }
    return written


def ensure_required_evidence(required_types: list[str], written: dict, available_refs: list[str] | None = None) -> None:
    refs = list(available_refs or []) + list(written.values())
    missing = [item for item in required_types if not _requirement_satisfied(item, written, refs)]
    if missing:
        raise MissingEvidenceError(f"missing required evidence: {', '.join(missing)}")


def _write(path: Path, data: dict) -> str:
    write_yaml(path, data)
    return str(path)


def _requirement_satisfied(requirement: str, written: dict, refs: list[str]) -> bool:
    if requirement in written and Path(written[requirement]).exists():
        return True
    normalized = requirement.lower()
    if _has_named_evidence_ref(refs, normalized):
        return True
    if "stateconsistencycheck" in normalized:
        return _ref_contains(refs, "STATE_CONSISTENCY_CHECK")
    if "stepmatrixview" in normalized:
        return _ref_contains(refs, "STEP_MATRIX_VIEW")
    if "retrospective" in normalized or "iteration synthesis" in normalized:
        return _ref_contains(refs, "POST_ROUND_RETROSPECTIVE_AND_ITERATION_SYNTHESIS")
    if "verification evidence" in normalized:
        return all(key in written and Path(written[key]).exists() for key in ["command_output", "test_output"])
    if ("analysis" in normalized or "report" in normalized) and "evidence" in normalized:
        return _has_manual_report_ref(refs)
    if "first_instruction" in normalized or "first instruction" in normalized:
        return _has_first_instruction_dogfood_ref(refs)
    return False


def _has_named_evidence_ref(refs: list[str], normalized_requirement: str) -> bool:
    candidates = {
        normalized_requirement,
        normalized_requirement.replace("_", "-"),
        normalized_requirement.replace("-", "_"),
    }
    for ref in refs:
        lowered = ref.lower()
        path = Path(lowered)
        stem = path.stem
        if stem in candidates or lowered.endswith(tuple(f"/{candidate}.yaml" for candidate in candidates)):
            return Path(ref).exists()
    return False


def _ref_contains(refs: list[str], fragment: str) -> bool:
    return any(fragment in ref for ref in refs)


def _has_manual_report_ref(refs: list[str]) -> bool:
    for ref in refs:
        lowered = ref.lower()
        if lowered.endswith((".md", ".yaml", ".yml", ".txt")) and (
            "evidence/" in lowered
            or "report" in lowered
            or "finding" in lowered
            or "analysis" in lowered
        ):
            return True
    return False


def _has_first_instruction_dogfood_ref(refs: list[str]) -> bool:
    for ref in refs:
        lowered = ref.lower().replace("_", "-")
        if "first-instruction" in lowered and "dogfood" in lowered:
            return True
    return False
