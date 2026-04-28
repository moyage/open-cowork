from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .change_package import read_change_package, update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
from .simple_yaml import load_yaml, write_yaml
from .agent_adoption import write_agent_adoption_pack
from .baseline import materialize_baseline
from .defaults import DEFAULT_SCOPE_OUT
from .contract import ScopeConflictError, scope_conflicts
from .step_matrix import STEP_LABELS

REQUIRED_FORBIDDEN_ACTIONS = [
    "no_truth_source_pollution",
    "no_executor_reviewer_merge",
    "no_executor_stable_write_authority",
    "no_step6_before_step5_ready",
]


@dataclass(frozen=True)
class PrepareChangeRequest:
    root: str | Path
    change_id: str
    goal: str
    scope_in: list[str]
    scope_out: list[str]
    verify_commands: list[str]
    source_docs: list[str] | None = None
    profile: str = "personal"
    title: str = ""


def prepare_change_package(request: PrepareChangeRequest) -> dict:
    package = read_change_package(request.root, request.change_id)
    root = Path(request.root)
    title = request.title or package.manifest.get("title") or request.change_id
    scope_in = request.scope_in or ["src/**", "tests/**"]
    scope_out = _merge_scope_out(request.scope_out)
    conflicts = scope_conflicts(scope_in, scope_out)
    if conflicts:
        raise ScopeConflictError(conflicts, change_id=request.change_id)
    verify_commands = request.verify_commands or []

    source_docs = list(request.source_docs or [])
    _write_markdown_files(package.path, request.change_id, title, request.goal, scope_in, scope_out, verify_commands, source_docs)
    contract = _build_contract(request.change_id, title, request.goal, scope_in, scope_out, verify_commands, request.profile)
    existing_bindings = load_yaml(package.path / "bindings.yaml") if (package.path / "bindings.yaml").exists() else {}
    bindings = _preserve_participant_bindings(existing_bindings, _build_bindings(request.change_id, request.profile))
    write_yaml(package.path / "contract.yaml", contract)
    write_yaml(package.path / "bindings.yaml", bindings)
    baseline = materialize_baseline(root, request.change_id)
    write_agent_adoption_pack(
        root,
        change_id=request.change_id,
        title=title,
        goal=request.goal,
        profile=request.profile,
        bindings=bindings,
    )

    manifest = update_manifest(
        request.root,
        request.change_id,
        title=title,
        status="step1-ready",
        current_step=1,
        source_docs=source_docs,
        target_validation_objects=contract["validation_objects"],
        readiness=_readiness_for_step1(package.path),
    )
    _materialize_prepare_step_reports(request.root, request.change_id)
    current = read_current_change(request.root).get("current_change") or {}
    entry = {
        **current,
        "change_id": request.change_id,
        "path": str(package.path.relative_to(root)),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
        "title": manifest.get("title"),
    }
    set_current_change(request.root, entry)
    upsert_change_entry(request.root, entry)
    set_maintenance_status(
        request.root,
        status=manifest.get("status"),
        current_change_active=manifest.get("status"),
        current_change_id=request.change_id,
    )
    return {
        "change_id": request.change_id,
        "path": str(package.path),
        "contract": contract,
        "bindings": bindings,
        "baseline": baseline,
    }


def _merge_scope_out(scope_out: list[str]) -> list[str]:
    merged = []
    for item in [*(scope_out or []), *DEFAULT_SCOPE_OUT]:
        if item not in merged:
            merged.append(item)
    return merged


def _readiness_for_step1(change_dir: Path) -> dict:
    intent = load_yaml(change_dir / "intent-confirmation.yaml") if (change_dir / "intent-confirmation.yaml").exists() else {}
    gates = load_yaml(change_dir / "human-gates.yaml") if (change_dir / "human-gates.yaml").exists() else {}
    approvals = gates.get("approvals", {}) if isinstance(gates, dict) else {}
    step1_approval = approvals.get(1) or approvals.get("1") or {}
    missing_items = []
    if intent.get("status") != "confirmed":
        missing_items.append("intent_confirmation")
    if step1_approval.get("status") != "approved":
        missing_items.append("step1_confirmation")
    return {"step1_entry_ready": True, "step6_entry_ready": False, "missing_items": missing_items}


def _preserve_participant_bindings(existing: dict, generated: dict) -> dict:
    if not existing.get("participants_profile_ref"):
        return generated
    preserved = {**generated}
    preserved["profile"] = existing.get("profile", generated.get("profile"))
    preserved["participants_profile_ref"] = existing.get("participants_profile_ref")
    preserved["steps"] = existing.get("steps", generated.get("steps", {}))
    return preserved


def _materialize_prepare_step_reports(root: str | Path, change_id: str) -> None:
    from .step_report import materialize_step_report

    materialize_step_report(root, change_id=change_id, step=1)


def _write_markdown_files(
    change_dir: Path,
    change_id: str,
    title: str,
    goal: str,
    scope_in: list[str],
    scope_out: list[str],
    verify_commands: list[str],
    source_docs: list[str],
) -> None:
    (change_dir / "intent.md").write_text(
        "\n".join([
            f"# {title}",
            "",
            "## Goal",
            goal,
            "",
            "## Change ID",
            change_id,
            "",
            "## Source Docs",
            *([f"- {item}" for item in source_docs] or ["- No source docs recorded."]),
            "",
        ]),
        encoding="utf-8",
    )
    (change_dir / "requirements.md").write_text(
        "\n".join([
            f"# Requirements for {change_id}",
            "",
            "## Scope In",
            *[f"- {item}" for item in scope_in],
            "",
            "## Scope Out",
            *[f"- {item}" for item in scope_out],
            "",
            "## Verification Commands",
            *([f"- `{item}`" for item in verify_commands] or ["- No automated command provided; record manual verification evidence."]),
            "",
            "## Source Docs",
            *([f"- {item}" for item in source_docs] or ["- No source docs recorded."]),
            "",
        ]),
        encoding="utf-8",
    )
    (change_dir / "design.md").write_text(
        "\n".join([
            f"# Design for {change_id}",
            "",
            "This change uses the open-cowork personal pilot path:",
            "",
            "1. Keep the business implementation inside scope_in.",
            "2. Record objective evidence after execution.",
            "3. Separate executor and final reviewer whenever possible.",
            "4. Archive only after verify and review pass.",
            "",
        ]),
        encoding="utf-8",
    )
    (change_dir / "tasks.md").write_text(
        "\n".join([
            f"# Tasks for {change_id}",
            "",
            f"- [ ] Step 5: {STEP_LABELS[5]} contract.yaml and bindings.yaml.",
            f"- [ ] Step 6: {STEP_LABELS[6]} inside scope and record evidence.",
            f"- [ ] Step 7: {STEP_LABELS[7]} and record verify.yaml.",
            f"- [ ] Step 8: {STEP_LABELS[8]} and record review.yaml.",
            f"- [ ] Step 9: {STEP_LABELS[9]} continuity context.",
            "",
        ]),
        encoding="utf-8",
    )


def _build_contract(
    change_id: str,
    title: str,
    goal: str,
    scope_in: list[str],
    scope_out: list[str],
    verify_commands: list[str],
    profile: str,
) -> dict:
    contract_scope_in = [*scope_in, f".governance/changes/{change_id}/evidence/**"]
    return {
        "schema": "execution-contract/v1",
        "change_id": change_id,
        "title": title,
        "objective": goal,
        "scope_in": contract_scope_in,
        "scope_out": scope_out,
        "allowed_actions": ["edit_files", "run_commands", "write_evidence"],
        "forbidden_actions": REQUIRED_FORBIDDEN_ACTIONS + [
            "expand_scope_without_review",
            "modify_external_agent_config",
        ],
        "validation_objects": [
            f".governance/changes/{change_id}/contract.yaml",
            f".governance/changes/{change_id}/bindings.yaml",
            *contract_scope_in,
        ],
        "verification": {
            "commands": verify_commands,
            "checks": [
                "All modified files stay within scope_in unless explicitly approved.",
                "Evidence is recorded before verify/review/archive.",
                "Executor does not self-approve final review.",
            ],
        },
        "evidence_expectations": {
            "required": ["command_output", "test_output", "changed_files_manifest"],
        },
        "role_constraints": {
            "profile": profile,
            "executor_must_not_be_final_reviewer": True,
            "stable_facts_write_authority": "maintainer",
        },
        "failure_policy": {"on_blocker": "halt_and_report"},
    }


def _build_bindings(change_id: str, profile: str) -> dict:
    return {
        "schema": "role-bindings/v1",
        "change_id": change_id,
        "profile": profile,
        "global": {
            "sponsor": "human-sponsor",
            "orchestrator": "orchestrator-agent",
            "analyst": "analyst-agent",
            "default_executor": "executor-agent",
            "default_verifier": "verifier-agent",
            "default_reviewer": "independent-reviewer",
            "default_maintainer": "maintainer-agent",
        },
        "steps": {
            "'1'": {"owner": "human-sponsor", "gate": "review-required", "human_gate": True},
            "'2'": {"owner": "analyst-agent", "gate": "approval-required", "human_gate": True},
            "'3'": {"owner": "architect-agent", "gate": "review-required", "human_gate": True},
            "'4'": {"owner": "orchestrator-agent", "gate": "review-required", "human_gate": False},
            "'5'": {"owner": "human-sponsor", "gate": "approval-required", "human_gate": True},
            "'6'": {"owner": "executor-agent", "gate": "auto-pass-to-step7", "human_gate": False, "isolation": "project-local"},
            "'7'": {"owner": "verifier-agent", "gate": "review-required", "human_gate": False},
            "'8'": {"owner": "independent-reviewer", "gate": "approval-required", "human_gate": True},
            "'9'": {"owner": "maintainer-agent", "gate": "approval-required", "human_gate": True},
        },
    }
