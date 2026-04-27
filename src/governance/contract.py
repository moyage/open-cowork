from __future__ import annotations

from pathlib import Path

from .simple_yaml import load_yaml

REQUIRED_CONTRACT_FIELDS = (
    "objective",
    "scope_in",
    "scope_out",
    "allowed_actions",
    "forbidden_actions",
    "validation_objects",
    "verification",
    "evidence_expectations",
)

REQUIRED_FORBIDDEN_ACTIONS = {
    "no_truth_source_pollution",
    "no_executor_reviewer_merge",
    "no_executor_stable_write_authority",
    "no_step6_before_step5_ready",
}


class ContractValidationError(ValueError):
    pass


class ScopeConflictError(ContractValidationError):
    def __init__(self, conflicts: list[str], *, change_id: str = ""):
        self.conflicts = conflicts
        self.change_id = change_id
        super().__init__("scope_in conflicts with scope_out: " + ", ".join(conflicts))


def load_contract(path: str | Path) -> dict:
    contract = load_yaml(path)
    errors = validate_contract(contract)
    if errors:
        raise ContractValidationError("; ".join(errors))
    return contract


def validate_contract(contract: dict) -> list[str]:
    errors = []
    for field in REQUIRED_CONTRACT_FIELDS:
        if field not in contract or contract[field] in (None, {}, []):
            errors.append(f"missing required field: {field}")
    if not isinstance(contract.get("objective"), str) or not contract.get("objective", "").strip():
        errors.append("objective must be a non-empty string")
    if not isinstance(contract.get("scope_in"), list):
        errors.append("scope_in must be a list")
    if not isinstance(contract.get("scope_out"), list):
        errors.append("scope_out must be a list")
    if isinstance(contract.get("scope_in"), list) and isinstance(contract.get("scope_out"), list):
        conflicts = _scope_conflicts(contract.get("scope_in", []), contract.get("scope_out", []))
        if conflicts:
            errors.append("scope_in conflicts with scope_out: " + ", ".join(conflicts))
    if not isinstance(contract.get("allowed_actions"), list):
        errors.append("allowed_actions must be a list")
    if not isinstance(contract.get("forbidden_actions"), list):
        errors.append("forbidden_actions must be a list")
    else:
        forbidden_actions = set(contract.get("forbidden_actions", []))
        missing_required_forbidden = sorted(REQUIRED_FORBIDDEN_ACTIONS - forbidden_actions)
        if missing_required_forbidden:
            errors.append(
                "forbidden_actions missing required governance guards: " + ", ".join(missing_required_forbidden)
            )
    if not isinstance(contract.get("validation_objects"), list) or not contract.get("validation_objects"):
        errors.append("validation_objects must be a non-empty list")
    verification = contract.get("verification")
    if not isinstance(verification, dict) or not isinstance(verification.get("checks"), list) or not isinstance(verification.get("commands", []), list):
        errors.append("verification must include list fields commands and checks")
    evidence = contract.get("evidence_expectations")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("required"), list) or not evidence.get("required"):
        errors.append("evidence_expectations must include a non-empty required list")
    role_constraints = contract.get("role_constraints")
    if role_constraints is not None and not isinstance(role_constraints, dict):
        errors.append("role_constraints must be a mapping when present")
    return errors


def scope_conflicts(scope_in: list[str], scope_out: list[str]) -> list[str]:
    return _scope_conflicts(scope_in, scope_out)


def _scope_conflicts(scope_in: list[str], scope_out: list[str]) -> list[str]:
    conflicts = []
    for include in scope_in:
        include_base = _scope_base(include)
        for exclude in scope_out:
            exclude_base = _scope_base(exclude)
            if include_base == exclude_base or include_base.startswith(exclude_base + "/") or exclude_base.startswith(include_base + "/"):
                conflicts.append(f"{include} overlaps {exclude}")
    return conflicts


def _scope_base(pattern: str) -> str:
    normalized = str(pattern).replace("\\", "/").strip("/")
    for suffix in ("/**", "/*"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized
