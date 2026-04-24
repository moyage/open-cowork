from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .change_package import read_change_package, update_manifest
from .index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
from .simple_yaml import write_yaml
from .agent_adoption import write_agent_adoption_pack

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
    scope_out = request.scope_out or [
        ".governance/index/**",
        ".governance/archive/**",
        ".governance/runtime/**",
    ]
    verify_commands = request.verify_commands or []

    source_docs = list(request.source_docs or [])
    _write_markdown_files(package.path, request.change_id, title, request.goal, scope_in, scope_out, verify_commands, source_docs)
    contract = _build_contract(request.change_id, title, request.goal, scope_in, scope_out, verify_commands, request.profile)
    bindings = _build_bindings(request.change_id, request.profile)
    write_yaml(package.path / "contract.yaml", contract)
    write_yaml(package.path / "bindings.yaml", bindings)
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
        status="step5-prepared",
        current_step=5,
        source_docs=source_docs,
        target_validation_objects=contract["validation_objects"],
        readiness={"step6_entry_ready": True, "missing_items": []},
    )
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
    return {"change_id": request.change_id, "path": str(package.path), "contract": contract, "bindings": bindings}


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
            "- [ ] Step 5: Confirm contract.yaml and bindings.yaml are acceptable.",
            "- [ ] Step 6: Execute inside scope and record evidence.",
            "- [ ] Step 7: Run verification and record verify.yaml.",
            "- [ ] Step 8: Request independent review and record review.yaml.",
            "- [ ] Step 9: Archive and carry forward continuity context.",
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
            "'5'": {"owner": "orchestrator", "gate": "human-or-agent-confirmation"},
            "'6'": {"owner": "executor", "gate": "contract-required", "isolation": "project-local"},
            "'7'": {"owner": "verifier", "gate": "evidence-required"},
            "'8'": {"owner": "reviewer", "gate": "independent-review-required"},
            "'9'": {"owner": "maintainer", "gate": "approved-review-required"},
        },
    }
