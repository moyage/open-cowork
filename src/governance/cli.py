from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def cmd_change_create(args):
    from governance.change_package import create_change_package
    from governance.index import ensure_governance_index, set_current_change, set_maintenance_status, upsert_change_entry

    root = Path(args.root)
    ensure_governance_index(root)
    package = create_change_package(root, args.change_id, title=args.title or "")
    change_entry = {
        "change_id": package.change_id,
        "path": str(package.path.relative_to(root)),
        "status": package.manifest.get("status"),
        "current_step": package.manifest.get("current_step"),
        "title": package.manifest.get("title"),
    }
    set_current_change(root, change_entry)
    upsert_change_entry(root, change_entry)
    set_maintenance_status(
        root,
        status=package.manifest.get("status"),
        current_change_active="draft",
        current_change_id=package.change_id,
    )
    print(f"Created change package {package.change_id} at {package.path}")
    return 0


def cmd_change_prepare(args):
    from governance.change_prepare import PrepareChangeRequest, prepare_change_package

    if not (args.goal or "").strip():
        print("--goal is required for 'ocw change prepare'.")
        return 1
    lifecycle_error = _active_change_lifecycle_error(args.root, args.change_id, getattr(args, "active_policy", None))
    if lifecycle_error:
        print(lifecycle_error)
        return 1

    payload = prepare_change_package(PrepareChangeRequest(
        root=args.root,
        change_id=args.change_id,
        title=args.title or "",
        goal=args.goal,
        scope_in=list(args.scope_in or []),
        scope_out=list(args.scope_out or []),
        verify_commands=list(args.verify_command or []),
        source_docs=list(args.source_doc or []),
        profile=args.profile,
    ))
    print(f"Change prepared: {payload['change_id']}")
    print("")
    print(_format_agent_handoff(payload["change_id"]))
    return 0


def _format_agent_handoff(change_id: str) -> str:
    return "\n".join([
        "Agent-first handoff ready.",
        "Read these files before continuing:",
        "- .governance/AGENTS.md",
        "- .governance/current-state.md",
        "- .governance/agent-playbook.md",
        f"- .governance/changes/{change_id}/contract.yaml",
        f"- .governance/changes/{change_id}/bindings.yaml",
        "",
        "Human control baseline before Step 6:",
        f"- ocw --root . participants setup --profile personal --change-id {change_id}",
        f"- ocw --root . intent capture --change-id {change_id} --project-intent \"Describe the real iteration intent\"",
        f"- ocw --root . intent confirm --change-id {change_id} --confirmed-by human-sponsor",
        f"- ocw --root . step report --change-id {change_id} --step 5",
        "",
        "Report project progress, owner, blocker, next action, and human decisions needed.",
        "Do not make the human copy long command prompts or memorize ocw commands.",
    ])


def cmd_pilot(args):
    target = Path(args.target or args.root).expanduser().resolve()
    lifecycle_error = _active_change_lifecycle_error(target, args.change_id, getattr(args, "active_policy", None))
    if lifecycle_error:
        print(lifecycle_error)
        return 1
    if not args.yes and not _confirm_pilot(target, args.change_id):
        print("Pilot cancelled.")
        return 1

    target.mkdir(parents=True, exist_ok=True)
    print("open-cowork pilot")
    print("")
    print(f"- target: {target}")
    print(f"- change_id: {args.change_id}")
    print("")
    cmd_init(argparse.Namespace(root=str(target)))
    create_exit = cmd_change_create(argparse.Namespace(root=str(target), change_id=args.change_id, title=args.title or args.change_id, active_policy=args.active_policy))
    if create_exit:
        return create_exit
    prepare_exit = cmd_change_prepare(argparse.Namespace(
        root=str(target),
        change_id=args.change_id,
        title=args.title or args.change_id,
        goal=args.goal,
        scope_in=list(args.scope_in or []),
        scope_out=list(args.scope_out or []),
        verify_command=list(args.verify_command or []),
        source_doc=[],
        profile=args.profile,
        active_policy=args.active_policy,
    ))
    if prepare_exit:
        return prepare_exit
    print("")
    validate_exit = cmd_contract_validate(argparse.Namespace(root=str(target), change_id=args.change_id, path=None))
    if validate_exit != 0:
        return validate_exit
    print("")
    cmd_status(argparse.Namespace(root=str(target)))
    print("")
    cmd_continuity_digest(argparse.Namespace(root=str(target), change_id=args.change_id, format="text"))
    print("")
    print("open-cowork pilot complete.")
    print("")
    print(_format_agent_handoff(args.change_id))
    return 0


def _confirm_pilot(target: Path, change_id: str) -> bool:
    print("open-cowork pilot")
    print("")
    print("This will initialize .governance/ and prepare a governed change package.")
    print("It will not modify application source files.")
    print("")
    print(f"- target: {target}")
    print(f"- change_id: {change_id}")
    answer = input("Continue? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _active_change_lifecycle_error(root: str | Path, requested_change_id: str | None, active_policy: str | None) -> str | None:
    from governance.index import read_current_change

    current_path = Path(root) / ".governance/index/current-change.yaml"
    if not current_path.exists():
        return None
    current = read_current_change(root)
    nested = current.get("current_change", {})
    if not isinstance(nested, dict):
        nested = {}
    active_change_id = current.get("current_change_id") or nested.get("change_id")
    active_status = current.get("status") or nested.get("status")
    if not active_change_id or str(active_status) in {"idle", "archived", "abandoned", "superseded", "none"}:
        return None
    if requested_change_id and str(active_change_id) == str(requested_change_id):
        return None
    if active_policy == "force":
        return None
    if active_policy in {"supersede", "abandon", "archive-first"}:
        return (
            "Active change lifecycle decision required: "
            f"active change '{active_change_id}' is '{active_status}', and policy '{active_policy}' requires an explicit lifecycle operation before switching."
        )
    return (
        "Active change lifecycle decision required: "
        f"active change '{active_change_id}' is '{active_status}'. "
        "Use --active-policy force only after deciding to override, or close/supersede/archive the active change first."
    )


def cmd_contract_validate(args):
    from governance.change_package import read_change_package
    from governance.contract import ContractValidationError, load_contract
    from governance.runtime_events import append_runtime_event

    try:
        contract_path = Path(args.path) if args.path else read_change_package(args.root, args.change_id).path / "contract.yaml"
        load_contract(contract_path)
        change_id = args.change_id or contract_path.parent.name
        append_runtime_event(
            args.root,
            change_id=change_id,
            event_type="contract_validate_pass",
            step=5,
            from_status="contract-present",
            to_status="contract-valid",
            actor_id="governance",
            refs=[str(contract_path.relative_to(Path(args.root)))],
            source_path=contract_path,
        )
        print(f"Contract valid: {contract_path}")
        return 0
    except (ValueError, ContractValidationError) as exc:
        contract_path = Path(args.path) if args.path else (
            Path(args.root) / ".governance" / "changes" / str(args.change_id) / "contract.yaml"
            if args.change_id else None
        )
        change_id = args.change_id or (contract_path.parent.name if contract_path else None)
        if change_id:
            append_runtime_event(
                args.root,
                change_id=change_id,
                event_type="contract_validate_fail",
                step=5,
                from_status="contract-present",
                to_status="contract-invalid",
                actor_id="governance",
                refs=[str(contract_path.relative_to(Path(args.root)))] if contract_path else [],
                source_path=contract_path,
            )
        print(f"Contract invalid: {exc}")
        return 1


def cmd_run(args):
    from governance.change_package import read_change_package, update_manifest
    from governance.index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
    from governance.run import AdapterRequest, run_change
    from governance.runtime_events import append_runtime_event

    package = read_change_package(args.root, args.change_id)
    previous_status = package.manifest.get("status")
    contract_path = package.path / "contract.yaml"
    request = AdapterRequest(
        change_id=package.change_id,
        contract_path=str(contract_path),
        working_directory=str(Path(args.root)),
        allowed_write_scope=[".governance/**", "src/**", "tests/**"],
        timeout_seconds=args.timeout_seconds,
        command=args.exec_command,
        command_output=args.command_output,
        test_output=args.test_output,
        artifacts={"created": list(args.created or []), "modified": list(args.modified or [])},
        evidence_refs=list(args.evidence_ref or []),
    )
    try:
        response = run_change(args.root, request)
    except Exception as exc:
        append_runtime_event(
            args.root,
            change_id=package.change_id,
            event_type="gate_blocked",
            step=6,
            from_status=previous_status,
            to_status="blocked",
            actor_id=package.manifest.get("roles", {}).get("executor") or "executor",
            event_suffix="step6",
            extra={"reason": str(exc)},
        )
        print(f"Run failed: {exc}")
        return 1
    manifest = update_manifest(args.root, package.change_id, status="step6-executed-pre-step7", current_step=6)
    current = read_current_change(args.root).get("current_change") or {}
    set_current_change(args.root, {
        **current,
        "change_id": package.change_id,
        "path": str(package.path.relative_to(Path(args.root))),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
    })
    upsert_change_entry(args.root, {
        "change_id": package.change_id,
        "path": str(package.path.relative_to(Path(args.root))),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
    })
    set_maintenance_status(
        args.root,
        status=manifest.get("status"),
        current_change_active=manifest.get("status"),
        current_change_id=package.change_id,
    )
    execution_summary_path = package.path / "evidence" / "execution-summary.yaml"
    append_runtime_event(
        args.root,
        change_id=package.change_id,
        event_type="run_completed",
        step=6,
        from_status=previous_status,
        to_status=manifest.get("status"),
        actor_id=package.manifest.get("roles", {}).get("executor") or "executor",
        refs=[str(execution_summary_path.relative_to(Path(args.root)))] if execution_summary_path.exists() else [],
        source_path=execution_summary_path if execution_summary_path.exists() else package.path / "manifest.yaml",
    )
    print(f"Run completed: {package.change_id} ({response.run_id})")
    return 0


def cmd_adopt(args):
    from governance.agent_adoption import build_adoption_plan

    if not (args.goal or "").strip():
        print("--goal is required for 'ocw adopt'.")
        return 1
    if not args.dry_run:
        print("ocw adopt currently requires --dry-run before mutating governance state.")
        return 1
    payload = build_adoption_plan(
        args.root,
        target=args.target or args.root,
        goal=args.goal,
        source_docs=list(args.source_doc or []),
        agent_inventory=list(args.agent or []),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print("open-cowork adoption plan")
    print("")
    print(f"- target: {payload['target']}")
    print(f"- candidate_change_id: {payload['candidate_change']['change_id']}")
    print(f"- active_change: {payload['active_change'].get('change_id')}")
    print(f"- lifecycle_decision_required: {payload['active_change']['requires_lifecycle_decision']}")
    print("")
    print("Recommended read set:")
    for item in payload["recommended_read_set"]:
        print(f"- {item}")
    return 0


def cmd_hygiene(args):
    from governance.hygiene import build_hygiene_report

    payload = build_hygiene_report(args.root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print("open-cowork hygiene")
    print("")
    print("Runtime generated:")
    for item in payload["runtime_generated"]:
        print(f"- {item}")
    print("")
    print("Agent handoff files:")
    for item in payload["agent_handoff_files"]:
        print(f"- {item}")
    print("")
    print("Pending docs:")
    for item in payload["pending_docs"]:
        print(f"- {item}")
    print("")
    print("Recommendations:")
    for item in payload["recommendations"]:
        print(f"- {item}")
    state_consistency = payload.get("state_consistency")
    if state_consistency:
        print("")
        print("State consistency:")
        print(f"- status: {state_consistency.get('status')}")
        for issue in state_consistency.get("issues", []):
            print(f"- {issue}")
    return 0


def cmd_participants_setup(args):
    from governance.participants import setup_participants_profile

    payload = setup_participants_profile(
        args.root,
        profile=args.profile,
        participant_specs=list(args.participant or []),
        change_id=args.change_id,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print("open-cowork participants profile")
    print("")
    print(f"- profile: {payload['profile']}")
    print("- participants_profile_ref: .governance/participants.yaml")
    if args.change_id:
        print(f"- bindings updated: .governance/changes/{args.change_id}/bindings.yaml")
    print("")
    print("9-step owner matrix:")
    for item in payload["step_owner_matrix"]:
        print(
            f"- Step {item['step']}: owner={item['primary_owner']} "
            f"reviewer={item['reviewer']} human_gate={str(item['human_gate']).lower()}"
        )
    return 0


def cmd_intent_capture(args):
    from governance.intent import capture_intent

    payload = capture_intent(
        args.root,
        change_id=args.change_id,
        project_intent=args.project_intent,
        requirements=list(args.requirement or []),
        optimizations=list(args.optimization or []),
        bugs=list(args.bug or []),
        scope_in=list(args.scope_in or []),
        scope_out=list(args.scope_out or []),
        acceptance=list(args.acceptance or []),
        risks=list(args.risk or []),
        open_questions=list(args.open_question or []),
        confirmed_by=args.confirmed_by,
        note=args.note or "",
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"Intent {payload['status']}: {payload['change_id']}")
    print(f"- ref: .governance/changes/{args.change_id}/intent-confirmation.yaml")
    print(f"- project_intent: {payload['project_intent']}")
    return 0


def cmd_intent_confirm(args):
    from governance.intent import confirm_intent

    payload = confirm_intent(args.root, change_id=args.change_id, confirmed_by=args.confirmed_by, note=args.note or "")
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"Intent confirmed: {payload['change_id']}")
    print(f"- confirmed_by: {payload['human_confirmation']['confirmed_by']}")
    print(f"- ref: .governance/changes/{args.change_id}/intent-confirmation.yaml")
    return 0


def cmd_step_report(args):
    from governance.step_report import materialize_step_report

    payload = materialize_step_report(args.root, change_id=args.change_id, step=args.step)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(f"Step report written: .governance/changes/{args.change_id}/step-reports/step-{payload['step']}.md")
    print(f"- owner: {payload['owner']}")
    print(f"- human_gate: {str(payload['human_gate']).lower()}")
    print(f"- recommended_next_action: {payload['recommended_next_action']}")
    return 0


def cmd_verify(args):
    from governance.verify import write_verify_result
    from governance.runtime_events import append_runtime_event

    try:
        payload = write_verify_result(args.root, args.change_id)
        print(f"Verify recorded: {payload['change_id']} -> {payload['summary']['status']}")
        return 0
    except Exception as exc:
        append_runtime_event(
            args.root,
            change_id=args.change_id,
            event_type="gate_blocked",
            step=7,
            from_status=None,
            to_status="blocked",
            actor_id="governance",
            event_suffix="step7",
            extra={"reason": str(exc)},
        )
        print(f"Verify failed: {exc}")
        return 1


def cmd_review(args):
    from governance.review import write_review_decision
    from governance.runtime_events import append_runtime_event

    try:
        payload = write_review_decision(
            args.root,
            args.change_id,
            decision=args.decision,
            reviewer=args.reviewer,
            rationale=args.rationale or "",
        )
        print(f"Review recorded: {payload['change_id']} -> {payload['decision']['status']}")
        return 0
    except Exception as exc:
        append_runtime_event(
            args.root,
            change_id=args.change_id,
            event_type="gate_blocked",
            step=8,
            from_status=None,
            to_status="blocked",
            actor_id=args.reviewer or "governance",
            event_suffix="step8",
            extra={"reason": str(exc)},
        )
        print(f"Review failed: {exc}")
        return 1


def cmd_archive(args):
    from governance.archive import archive_change
    from governance.runtime_events import append_runtime_event

    try:
        receipt = archive_change(args.root, args.change_id)
        print(f"Archived change {receipt['change_id']} at {receipt['archived_at']}")
        return 0
    except Exception as exc:
        append_runtime_event(
            args.root,
            change_id=args.change_id,
            event_type="gate_blocked",
            step=9,
            from_status=None,
            to_status="blocked",
            actor_id="governance",
            event_suffix="step9",
            extra={"reason": str(exc)},
        )
        print(f"Archive failed: {exc}")
        return 1


def cmd_init(args):
    from governance.index import ensure_governance_index

    ensure_governance_index(args.root)
    print(f"Initialized open-cowork governance in {args.root}/.governance")


def cmd_version(args):
    project_root = Path(__file__).resolve().parents[2]
    version = _read_project_version(project_root)
    print(f"open-cowork {version}")
    print(f"python: {sys.executable}")
    print(f"cli: {Path(sys.argv[0]).resolve()}")
    print(f"project_root: {project_root}")
    return 0


def _read_project_version(project_root: Path) -> str:
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        match = re.search(r'^version = "([^"]+)"', pyproject_path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1)
    try:
        from importlib.metadata import version

        return version("open-cowork")
    except Exception:
        return "unknown"


def cmd_onboard(args):
    target = _resolve_onboard_target(args)
    mode = args.mode or "quickstart"

    if mode == "manual":
        print(_format_manual_onboard_plan(target))
        return 0

    if not args.yes and not _confirm_onboard(target, mode):
        print("Onboarding cancelled.")
        return 1

    target.mkdir(parents=True, exist_ok=True)
    print("open-cowork onboard")
    print("")
    print("open-cowork 是一个本地优先的协作治理框架。")
    print("它会初始化 .governance/，不会修改你的业务代码。")
    print("")
    print(f"- target: {target}")
    print(f"- mode: {mode}")
    print("")
    cmd_init(argparse.Namespace(root=str(target)))
    print("")
    cmd_status(argparse.Namespace(root=str(target)))
    if not args.no_diagnose:
        print("")
        cmd_diagnose_session(argparse.Namespace(
            root=str(target),
            change_id=None,
            context_budget=args.context_budget,
        ))
    if args.create_demo_change:
        demo_change_id = args.demo_change_id or "current-iteration"
        print("")
        cmd_change_create(argparse.Namespace(root=str(target), change_id=demo_change_id, title="Personal domain pilot"))
    print("")
    print(_format_onboard_next_steps(target, mode, args.create_demo_change, args.demo_change_id or "current-iteration"))
    return 0


def _resolve_onboard_target(args) -> Path:
    if args.target:
        return Path(args.target).expanduser().resolve()
    if args.yes:
        return Path(args.root).expanduser().resolve()
    value = input("Target project path [.]: ").strip() or "."
    return Path(value).expanduser().resolve()


def _confirm_onboard(target: Path, mode: str) -> bool:
    print("open-cowork onboard")
    print("")
    print("This will initialize .governance/ in the target project.")
    print("It will not modify application source files.")
    print("")
    print(f"- target: {target}")
    print(f"- mode: {mode}")
    answer = input("Continue? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _format_manual_onboard_plan(target: Path) -> str:
    return "\n".join([
        "# open-cowork onboard",
        "",
        "## Manual onboarding plan",
        f"- target: {target}",
        "",
        "Commands to run:",
        f"- ocw --root \"{target}\" init",
        f"- ocw --root \"{target}\" status",
        f"- ocw --root \"{target}\" diagnose-session",
        "",
        "Optional next step:",
        f"- ocw --root \"{target}\" adopt --target \"{target}\" --goal \"Describe the project iteration to govern\" --dry-run",
    ]) + "\n"


def _format_onboard_next_steps(target: Path, mode: str, created_demo_change: bool, demo_change_id: str) -> str:
    lines = [
        "open-cowork onboard complete.",
        "",
        "Agent next action:",
        "- Use ocw adopt to build an Agent-first adoption plan before mutating governance state.",
        "- After a change exists, use participants setup, intent confirm, and step report before Step 6.",
    ]
    if not created_demo_change:
        lines.append(f"- ocw --root \"{target}\" adopt --target \"{target}\" --goal \"Describe the project iteration to govern\" --dry-run")
        lines.append(f"- ocw --root \"{target}\" status")
    else:
        lines.append(f"- ocw --root \"{target}\" status")
        lines.append(f"- ocw --root \"{target}\" continuity digest --change-id {demo_change_id}")
    if mode == "personal":
        lines.extend([
            "",
            "Personal mode reminder:",
            "- Keep executor and final reviewer separated when possible.",
            "- Use a second Agent, another session, or a human for independent review.",
        ])
    elif mode == "team":
        lines.extend([
            "",
            "Team mode minimum agreement:",
            "- Bind every collaboration to a change-id.",
            "- Record evidence before review.",
            "- Do not let the executor self-approve final review.",
            "- Close out before starting the next round.",
        ])
    lines.extend([
        "",
        "Read next:",
        "- docs/getting-started.md",
    ])
    return "\n".join(lines)


def cmd_status(args):
    from governance.contract import ContractValidationError
    from governance.index import read_current_change
    from governance.simple_yaml import load_yaml
    from governance.step_matrix import format_status_snapshot_view, write_status_snapshot

    try:
        if getattr(args, "sync_current_state", False):
            from governance.current_state import sync_current_state

            path = sync_current_state(args.root)
            print(f"Current state synced: {path}")
            return
        current = read_current_change(args.root)
        nested_current = current.get("current_change", {})
        has_active_change = bool(current.get("current_change_id"))
        if isinstance(nested_current, dict) and nested_current:
            has_active_change = has_active_change or bool(
                nested_current.get("change_id") or nested_current.get("current_change_id")
            )
        if not has_active_change:
            maintenance_path = Path(args.root) / ".governance" / "index" / "maintenance-status.yaml"
            print("# open-cowork status")
            print("")
            print("- lifecycle: idle")
            if maintenance_path.exists():
                maintenance = load_yaml(maintenance_path)
                print(f"- last_archived_change: {maintenance.get('last_archived_change')}")
                print(f"- last_archive_at: {maintenance.get('last_archive_at')}")
            print("- next_action: create or set an active change before running step matrix view")
            return
        snapshot_path = write_status_snapshot(args.root)
        snapshot = load_yaml(snapshot_path)
        print(format_status_snapshot_view(snapshot))
    except ContractValidationError as e:
        current = read_current_change(args.root)
        print(_format_draft_status_view(args.root, current, str(e)))
    except Exception as e:
        print(f"Status check failed: {e}")
        print("Tip: Have you run 'ocw init' or set a current change?")


def _format_draft_status_view(root: str | Path, current: dict, contract_error: str) -> str:
    from governance.simple_yaml import load_yaml

    nested_current = current.get("current_change", {})
    if not isinstance(nested_current, dict):
        nested_current = {}
    change_id = current.get("current_change_id") or nested_current.get("change_id")
    change_dir = Path(root) / ".governance" / "changes" / str(change_id)
    manifest = load_yaml(change_dir / "manifest.yaml") if change_id else {}
    title = manifest.get("title") or change_id or "(untitled change)"
    current_status = current.get("status") or nested_current.get("status") or manifest.get("status") or "drafting"
    current_step = current.get("current_step") or nested_current.get("current_step") or manifest.get("current_step") or 5
    owner = manifest.get("owner") or "orchestrator"
    lines = [
        "# open-cowork status",
        "",
        "## Draft change snapshot",
        f"- change_id: {change_id}",
        "- current_phase: Phase 2 / 方案与准备",
        f"- current_step: {current_step}",
        f"- current_status: {current_status}",
        f"- current_owner: {owner}",
        "- waiting_on: contract.yaml and bindings.yaml",
        "- next_decision: Step 5 / Approve the start",
        "- human_intervention_required: true",
        f"- project_summary: {title}",
        "",
        "## Progress",
        "- completed_steps: none",
        "- remaining_steps: 5, 6, 7, 8, 9",
        "",
        "## Blockers",
        "- contract draft is incomplete and not ready for execution",
        "",
        "## Next action",
        "- next_action: complete contract.yaml and bindings.yaml before runtime-status, run, verify, review, or archive",
    ]
    return "\n".join(lines) + "\n"


def cmd_continuity_launch_input(args):
    from governance.continuity import materialize_continuity_launch_input

    output_path = materialize_continuity_launch_input(args.root, args.change_id)
    print(f"Continuity launch input written: {output_path}")
    return 0


def cmd_continuity_round_entry_summary(args):
    from governance.continuity import materialize_round_entry_input_summary

    output_path = materialize_round_entry_input_summary(args.root, args.change_id)
    print(f"Round entry summary written: {output_path}")
    return 0


def cmd_continuity_handoff_package(args):
    from governance.continuity import materialize_handoff_package

    output_path = materialize_handoff_package(args.root, args.change_id)
    print(f"Handoff package written: {output_path}")
    return 0


def cmd_continuity_owner_transfer_prepare(args):
    from governance.continuity import prepare_owner_transfer_continuity

    output_path = prepare_owner_transfer_continuity(
        args.root,
        change_id=args.change_id,
        target_role=args.target_role,
        outgoing_owner=args.outgoing_owner,
        incoming_owner=args.incoming_owner,
        reason=args.reason,
        initiated_by=args.initiated_by,
    )
    print(f"Owner transfer continuity written: {output_path}")
    return 0


def cmd_continuity_owner_transfer_accept(args):
    from governance.continuity import accept_owner_transfer_continuity

    payload = accept_owner_transfer_continuity(
        args.root,
        change_id=args.change_id,
        accepted_by=args.accepted_by,
        note=args.note or "",
    )
    print(f"Owner transfer accepted: {payload['change_id']} -> {payload['acceptance']['status']}")
    return 0


def cmd_continuity_increment_package(args):
    from governance.continuity import materialize_increment_package

    output_path = materialize_increment_package(
        args.root,
        change_id=args.change_id,
        reason=args.reason,
        segment_owner=args.segment_owner,
        segment_label=args.segment_label,
        new_findings=list(args.new_finding or []),
        invalidated_assumptions=list(args.invalidated_assumption or []),
        new_risks=list(args.new_risk or []),
        blockers=list(args.blocker or []),
        next_followups=list(args.next_followup or []),
    )
    print(f"Increment package written: {output_path}")
    return 0


def cmd_continuity_closeout_packet(args):
    from governance.continuity import materialize_closeout_packet

    output_path = materialize_closeout_packet(
        args.root,
        change_id=args.change_id,
        closeout_statement=args.closeout_statement,
        delivered_scope=list(args.delivered_scope or []),
        deferred_scope=list(args.deferred_scope or []),
        key_outcomes=list(args.key_outcome or []),
        unresolved_items=list(args.unresolved_item or []),
        next_direction=args.next_direction,
        attention_points=list(args.attention_point or []),
        carry_forward_items=list(args.carry_forward_item or []),
        operator_summary=args.operator_summary,
        sponsor_summary=args.sponsor_summary,
    )
    print(f"Closeout packet written: {output_path}")
    return 0


def cmd_continuity_sync_packet(args):
    from governance.continuity import materialize_sync_packet

    output_path = materialize_sync_packet(
        args.root,
        change_id=args.change_id,
        source_kind=args.source_kind,
        sync_kind=args.sync_kind,
        target_layer=args.target_layer,
        target_scope=args.target_scope,
        urgency=args.urgency,
        headline=args.headline,
        delivered_scope=list(args.delivered_scope or []),
        pending_scope=list(args.pending_scope or []),
        requested_attention=list(args.requested_attention or []),
        requested_decisions=list(args.requested_decision or []),
        next_owner_suggestion=args.next_owner_suggestion,
        next_action_suggestion=args.next_action_suggestion,
    )
    print(f"Sync packet written: {output_path}")
    return 0


def cmd_continuity_sync_history(args):
    from governance.continuity import append_sync_history

    output_path = append_sync_history(args.root, change_id=args.change_id, source_kind=args.source_kind)
    print(f"Sync history written: {output_path}")
    return 0


def cmd_continuity_sync_history_query(args):
    from governance.continuity import read_sync_history, read_sync_history_across_months

    if args.all_months:
        payload = read_sync_history_across_months(
            args.root,
            change_id=args.change_id,
            source_kind=args.source_kind,
            sync_kind=args.sync_kind,
            summary_by=args.summary_by,
            summary_only=args.summary_only,
        )
    else:
        payload = read_sync_history(
            args.root,
            month=args.month,
            change_id=args.change_id,
            source_kind=args.source_kind,
            sync_kind=args.sync_kind,
            summary_by=args.summary_by,
            summary_only=args.summary_only,
        )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0

    print(f"Sync history month: {payload['month']}")
    print(f"matched events: {payload['summary']['matched_events']}")
    if any(value is not None for value in payload["filters"].values()):
        print(f"filters: {payload['filters']}")
    grouped_summary = payload.get("grouped_summary")
    if grouped_summary:
        print(f"grouped summary by: {grouped_summary['group_by']}")
        for group in grouped_summary.get("groups", []):
            print(
                f"- {group.get('group_key')} "
                f"events={group.get('event_count')} "
                f"distinct_changes={group.get('distinct_change_count')} "
                f"latest={group.get('latest_headline')} "
                f"latest_change={group.get('latest_change_id')} "
                f"latest_sync_kind={group.get('latest_sync_kind')}"
            )
    if not args.summary_only:
        for event in payload["events"]:
            print(
                f"- {event.get('recorded_at')} {event.get('change_id')} "
                f"[{event.get('source_kind')}/{event.get('sync_kind')}] {event.get('headline')}"
            )
    return 0


def cmd_continuity_sync_history_months(args):
    from governance.continuity import list_sync_history_months

    months = list_sync_history_months(args.root)
    payload = {
        "schema": "sync-history-months/v1",
        "months": months,
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    joined = ", ".join(months) if months else "(empty)"
    print(f"Sync history months: {joined}")
    return 0


def cmd_continuity_export_sync_packet(args):
    from governance.continuity import export_sync_packet

    output_path = export_sync_packet(
        args.root,
        change_id=args.change_id,
        source_kind=args.source_kind,
        output_dir=args.output_dir,
    )
    print(f"Sync packet exported: {output_path}")
    return 0


def cmd_continuity_digest(args):
    from governance.contract import ContractValidationError
    from governance.continuity import resolve_continuity_digest

    try:
        payload = resolve_continuity_digest(args.root, args.change_id)
    except ContractValidationError:
        print(_format_draft_digest_guidance(args.root, args.change_id))
        return 0
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0

    print(f"Continuity digest: {payload['change_id']} ({payload['digest_kind']})")
    print(f"selected by: {payload['selected_by']}")
    print(f"headline: {payload['summary'].get('headline')}")
    print(f"status: {payload['summary'].get('status')} / {payload['summary'].get('phase')}")
    print(f"recommended reading: {payload['recommended_reading'].get('primary_ref')}")
    recent_sync_summary = payload.get("recent_sync_summary")
    if recent_sync_summary:
        print(
            "recent sync: "
            f"{recent_sync_summary.get('total_events')} events / "
            f"{recent_sync_summary.get('latest_sync_kind')} -> "
            f"{recent_sync_summary.get('latest_target_layer')} / "
            f"{recent_sync_summary.get('latest_headline')}"
        )
    recent_sync_grouped_summary = payload.get("recent_sync_grouped_summary")
    if recent_sync_grouped_summary:
        print(f"recent sync groups: {recent_sync_grouped_summary.get('group_by')}")
        for group in recent_sync_grouped_summary.get("groups", []):
            print(
                "- "
                f"{group.get('group_key')} "
                f"events={group.get('event_count')} "
                f"distinct_changes={group.get('distinct_change_count')} "
                f"latest_change={group.get('latest_change_id')} "
                f"latest_sync_kind={group.get('latest_sync_kind')}"
            )
    recent_runtime_events = payload.get("recent_runtime_events", [])
    if recent_runtime_events:
        print("recent events:")
        for event in recent_runtime_events:
            print(f"- {event.get('event_type')} -> {event.get('to_status')}")
    for ref in payload["recommended_reading"].get("secondary_refs", []):
        print(f"- {ref}")
    return 0


def _format_draft_digest_guidance(root: str | Path, change_id: str | None) -> str:
    from governance.index import read_current_change
    from governance.simple_yaml import load_yaml

    current = read_current_change(root)
    nested_current = current.get("current_change", {})
    if not isinstance(nested_current, dict):
        nested_current = {}
    resolved_change_id = change_id or current.get("current_change_id") or nested_current.get("change_id")
    change_dir = Path(root) / ".governance" / "changes" / str(resolved_change_id)
    manifest = load_yaml(change_dir / "manifest.yaml") if resolved_change_id else {}
    title = manifest.get("title") or resolved_change_id or "(untitled change)"
    lines = [
        "# open-cowork continuity digest",
        "",
        "Continuity digest unavailable for draft change.",
        "",
        f"- change_id: {resolved_change_id}",
        f"- project_summary: {title}",
        "- reason: contract.yaml is still a draft, so runtime continuity projections are not ready",
        "",
        "## Recommended next commands",
        "- ocw --root . status",
        "- ocw --root . diagnose-session",
        "- complete contract.yaml and bindings.yaml before using runtime-status, timeline, handoff, or digest",
    ]
    return "\n".join(lines) + "\n"


def cmd_runtime_status(args):
    from governance.runtime_status import materialize_runtime_status

    try:
        result = materialize_runtime_status(args.root, args.change_id)
        if args.format == "json":
            print(json.dumps(result["change_status"], ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(result["change_status"]), end="")
            return 0
        print(f"Runtime status written: {result['change_status_path']}")
        return 0
    except Exception as exc:
        print(f"Runtime status failed: {exc}")
        return 1


def cmd_timeline(args):
    from governance.runtime_status import materialize_timeline

    try:
        result = materialize_timeline(args.root, args.change_id)
        if args.format == "json":
            print(json.dumps(result["payload"], ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(result["payload"]), end="")
            return 0
        print(f"Timeline written: {result['path']}")
        return 0
    except Exception as exc:
        print(f"Timeline failed: {exc}")
        return 1


def cmd_diagnose_session(args):
    from governance.hermes_recovery import diagnose_hermes_execution_stall

    try:
        diagnosis = diagnose_hermes_execution_stall(
            args.root,
            context_budget_tokens=args.context_budget,
            change_id=args.change_id,
        )
        print("# Session Execution Diagnosis")
        print("")
        print(f"- lifecycle_phase: {diagnosis.get('lifecycle_phase')}")
        print(f"- target_change_id: {diagnosis.get('target_change_id')}")
        budget = diagnosis.get("context_budget", {})
        print(f"- context_budget_tokens: {budget.get('budget_tokens')}")
        print(f"- full_scan_estimated_tokens: {budget.get('full_scan_estimated_tokens')}")
        print(f"- recommended_set_estimated_tokens: {budget.get('recommended_set_estimated_tokens')}")
        duplicate = diagnosis.get("duplicate_surface", {})
        print(f"- duplicate_identical_files: {duplicate.get('identical_count')}")
        print("")
        print("## Root causes")
        for item in diagnosis.get("root_causes", []):
            print(f"- {item.get('id')}: {item.get('summary')}")
        print("")
        print("## Recommended read set")
        for item in diagnosis.get("recommended_read_set", []):
            print(f"- {item.get('path')} ({item.get('role')})")
        print("")
        print("## Immediate actions")
        for item in diagnosis.get("immediate_actions", []):
            print(f"- [{item.get('order')}] {item.get('action')}: {item.get('detail')}")
    except Exception as e:
        print(f"Session diagnosis failed: {e}")


def cmd_session_recovery_packet(args):
    from governance.hermes_recovery import materialize_hermes_recovery_packet

    try:
        output_path = materialize_hermes_recovery_packet(
            args.root,
            context_budget_tokens=args.context_budget,
            change_id=args.change_id,
            output_path=args.output,
        )
        print(f"Session recovery packet written: {output_path}")
    except Exception as e:
        print(f"Packet generation failed: {e}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="open-cowork CLI")
    parser.add_argument("--root", default=".", help="Project root directory")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Initialize minimum governance directory")
    subparsers.add_parser("propose", help="Create an intent draft")
    subparsers.add_parser("version", help="Show open-cowork version and command paths")

    for command_name in ("onboard", "setup"):
        p_onboard = subparsers.add_parser(command_name, help="Run interactive or scripted onboarding")
        p_onboard.add_argument("--target", default=None, help="Target project directory")
        p_onboard.add_argument(
            "--mode",
            choices=["quickstart", "personal", "team", "manual"],
            default="quickstart",
            help="Onboarding mode",
        )
        p_onboard.add_argument("--yes", action="store_true", help="Skip confirmation prompts")
        p_onboard.add_argument("--no-diagnose", action="store_true", help="Skip session diagnosis")
        p_onboard.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
        p_onboard.add_argument("--create-demo-change", action="store_true", help="Create a demo change after init")
        p_onboard.add_argument("--demo-change-id", default="current-iteration", help="Demo change id")

    p_pilot = subparsers.add_parser("pilot", help="Prepare a personal-domain pilot change in one command")
    p_pilot.add_argument("--target", default=None, help="Target project directory")
    p_pilot.add_argument("--change-id", default="current-iteration", help="Change identifier")
    p_pilot.add_argument("--title", default="Current iteration", help="Change title")
    p_pilot.add_argument("--goal", required=True, help="Pilot goal")
    p_pilot.add_argument("--scope-in", action="append", default=[], help="Allowed implementation path or glob")
    p_pilot.add_argument("--scope-out", action="append", default=[], help="Excluded path or glob")
    p_pilot.add_argument("--verify-command", action="append", default=[], help="Verification command")
    p_pilot.add_argument("--profile", choices=["personal", "team"], default="personal", help="Role binding profile")
    p_pilot.add_argument("--active-policy", choices=["continue", "supersede", "abandon", "archive-first", "force"], default=None, help="Policy for unresolved active change conflicts")
    p_pilot.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    p_adopt = subparsers.add_parser("adopt", help="Build an Agent-first adoption plan")
    p_adopt.add_argument("--target", default=None, help="Target project directory")
    p_adopt.add_argument("--goal", required=True, help="Natural-language adoption goal")
    p_adopt.add_argument("--source-doc", action="append", default=[], help="Source document path")
    p_adopt.add_argument("--agent", action="append", default=[], help="Available personal-domain agent or tool")
    p_adopt.add_argument("--dry-run", action="store_true", help="Plan without mutating governance state")
    p_adopt.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    for command_name in ("hygiene", "doctor"):
        p_hygiene = subparsers.add_parser(command_name, help="Classify governance artifacts and repository hygiene")
        p_hygiene.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
        p_hygiene.add_argument("--state-consistency", action="store_true", help="Include human-readable state consistency checks")

    p_participants = subparsers.add_parser("participants", help="Configure human and Agent participants")
    p_participants_sub = p_participants.add_subparsers(dest="subcmd")
    p_participants_setup = p_participants_sub.add_parser("setup", help="Write a participants profile and 9-step owner matrix")
    p_participants_setup.add_argument("--profile", choices=["personal", "team"], default="personal", help="Participants profile")
    p_participants_setup.add_argument("--participant", action="append", default=[], help="Participant spec, e.g. codex:executor,verifier")
    p_participants_setup.add_argument("--change-id", default=None, help="Optional change id whose bindings.yaml should be updated")
    p_participants_setup.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_intent = subparsers.add_parser("intent", help="Capture and confirm project intent")
    p_intent_sub = p_intent.add_subparsers(dest="subcmd")
    p_intent_capture = p_intent_sub.add_parser("capture", help="Write human-visible intent confirmation materials")
    p_intent_capture.add_argument("--change-id", required=True, help="Target change id")
    p_intent_capture.add_argument("--project-intent", default=None, help="Project intent summary")
    p_intent_capture.add_argument("--requirement", action="append", default=[], help="Requirement item")
    p_intent_capture.add_argument("--optimization", action="append", default=[], help="Optimization item")
    p_intent_capture.add_argument("--bug", action="append", default=[], help="Bug fix item")
    p_intent_capture.add_argument("--scope-in", action="append", default=[], help="Scope-in item")
    p_intent_capture.add_argument("--scope-out", action="append", default=[], help="Scope-out item")
    p_intent_capture.add_argument("--acceptance", action="append", default=[], help="Acceptance criterion")
    p_intent_capture.add_argument("--risk", action="append", default=[], help="Risk item")
    p_intent_capture.add_argument("--open-question", action="append", default=[], help="Open question")
    p_intent_capture.add_argument("--confirmed-by", default=None, help="Actor confirming the captured intent")
    p_intent_capture.add_argument("--note", default="", help="Confirmation note")
    p_intent_capture.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_intent_confirm = p_intent_sub.add_parser("confirm", help="Confirm existing intent materials")
    p_intent_confirm.add_argument("--change-id", required=True, help="Target change id")
    p_intent_confirm.add_argument("--confirmed-by", required=True, help="Human or sponsor confirming the intent")
    p_intent_confirm.add_argument("--note", default="", help="Confirmation note")
    p_intent_confirm.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    p_step = subparsers.add_parser("step", help="Create human-visible step reports")
    p_step_sub = p_step.add_subparsers(dest="subcmd")
    p_step_report = p_step_sub.add_parser("report", help="Write a report for a 9-step workflow step")
    p_step_report.add_argument("--change-id", required=True, help="Target change id")
    p_step_report.add_argument("--step", type=int, default=None, help="Step number, defaults to current step")
    p_step_report.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_change = subparsers.add_parser("change", help="Change package management")
    p_change.add_argument("subcmd", choices=["create", "prepare"], help="Create or prepare change package")
    p_change.add_argument("change_id", help="Change identifier")
    p_change.add_argument("--title", default="", help="Optional change title")
    p_change.add_argument("--goal", default="", help="Change goal for generated authoring files")
    p_change.add_argument("--scope-in", action="append", default=[], help="Allowed implementation path or glob")
    p_change.add_argument("--scope-out", action="append", default=[], help="Excluded path or glob")
    p_change.add_argument("--verify-command", action="append", default=[], help="Verification command")
    p_change.add_argument("--source-doc", action="append", default=[], help="Source document path")
    p_change.add_argument("--active-policy", choices=["continue", "supersede", "abandon", "archive-first", "force"], default=None, help="Policy for unresolved active change conflicts")
    p_change.add_argument("--profile", choices=["personal", "team"], default="personal", help="Role binding profile")

    p_contract = subparsers.add_parser("contract", help="Contract management")
    p_contract_sub = p_contract.add_subparsers(dest="subcmd")
    p_contract_validate = p_contract_sub.add_parser("validate", help="Validate contract for a change")
    p_contract_validate.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_contract_validate.add_argument("--path", default=None, help="Optional explicit contract path")

    p_run = subparsers.add_parser("run", help="Execute change adapter")
    p_run.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_run.add_argument("--timeout-seconds", type=int, default=60, help="Execution timeout in seconds")
    p_run.add_argument("--command", dest="exec_command", default=None, help="Command description for evidence")
    p_run.add_argument("--command-output", default="", help="Command output summary")
    p_run.add_argument("--test-output", default="", help="Test output summary")
    p_run.add_argument("--created", action="append", default=[], help="Created artifact path")
    p_run.add_argument("--modified", action="append", default=[], help="Modified artifact path")
    p_run.add_argument("--evidence-ref", action="append", default=[], help="Additional evidence reference path")

    p_verify = subparsers.add_parser("verify", help="Verify execution results")
    p_verify.add_argument("--change-id", required=True, help="Target change id")

    p_review = subparsers.add_parser("review", help="Review and decide on change")
    p_review.add_argument("--change-id", required=True, help="Target change id")
    p_review.add_argument("--decision", choices=["approve", "reject", "revise"], required=True, help="Review decision")
    p_review.add_argument("--reviewer", required=True, help="Reviewer identifier")
    p_review.add_argument("--rationale", default="", help="Decision rationale")

    p_archive = subparsers.add_parser("archive", help="Archive and refresh state")
    p_archive.add_argument("--change-id", required=True, help="Target change id")
    p_status = subparsers.add_parser("status", help="Show current step, gate status, and blockers")
    p_status.add_argument("--sync-current-state", action="store_true", help="Refresh .governance/current-state.md from current index/runtime state")
    p_runtime_status = subparsers.add_parser("runtime-status", help="Write machine-readable runtime status snapshot")
    p_runtime_status.add_argument("--change-id", required=True, help="Target change id")
    p_runtime_status.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_timeline = subparsers.add_parser("timeline", help="Write machine-readable runtime timeline")
    p_timeline.add_argument("--change-id", required=True, help="Target change id")
    p_timeline.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_continuity = subparsers.add_parser("continuity", help="Materialize minimum continuity outputs")
    p_continuity_sub = p_continuity.add_subparsers(dest="subcmd")
    p_continuity_launch = p_continuity_sub.add_parser("launch-input", help="Write continuity launch input yaml")
    p_continuity_launch.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_continuity_round = p_continuity_sub.add_parser("round-entry-summary", help="Write round entry summary yaml")
    p_continuity_round.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_continuity_handoff = p_continuity_sub.add_parser("handoff-package", help="Write handoff package yaml")
    p_continuity_handoff.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_continuity_owner_transfer = p_continuity_sub.add_parser("owner-transfer", help="Manage owner transfer continuity")
    p_continuity_owner_transfer_sub = p_continuity_owner_transfer.add_subparsers(dest="owner_transfer_subcmd")
    p_owner_transfer_prepare = p_continuity_owner_transfer_sub.add_parser("prepare", help="Write owner transfer continuity yaml")
    p_owner_transfer_prepare.add_argument("--change-id", required=True, help="Target change id")
    p_owner_transfer_prepare.add_argument("--target-role", required=True, help="Transferred role")
    p_owner_transfer_prepare.add_argument("--outgoing-owner", required=True, help="Current owner id")
    p_owner_transfer_prepare.add_argument("--incoming-owner", required=True, help="Incoming owner id")
    p_owner_transfer_prepare.add_argument("--reason", required=True, help="Transfer reason")
    p_owner_transfer_prepare.add_argument("--initiated-by", required=True, help="Transfer initiator id")
    p_owner_transfer_accept = p_continuity_owner_transfer_sub.add_parser("accept", help="Accept pending owner transfer continuity")
    p_owner_transfer_accept.add_argument("--change-id", required=True, help="Target change id")
    p_owner_transfer_accept.add_argument("--accepted-by", required=True, help="Receiver accepting transfer")
    p_owner_transfer_accept.add_argument("--note", default="", help="Optional acceptance note")
    p_continuity_increment = p_continuity_sub.add_parser("increment-package", help="Write increment package yaml")
    p_continuity_increment.add_argument("--change-id", required=True, help="Target change id")
    p_continuity_increment.add_argument("--reason", required=True, help="Increment reason")
    p_continuity_increment.add_argument("--segment-owner", required=True, help="Segment owner id")
    p_continuity_increment.add_argument("--segment-label", required=True, help="Segment label")
    p_continuity_increment.add_argument("--new-finding", action="append", default=[], help="New finding")
    p_continuity_increment.add_argument("--invalidated-assumption", action="append", default=[], help="Invalidated assumption")
    p_continuity_increment.add_argument("--new-risk", action="append", default=[], help="New risk")
    p_continuity_increment.add_argument("--blocker", action="append", default=[], help="Blocker")
    p_continuity_increment.add_argument("--next-followup", action="append", default=[], help="Next followup")
    p_continuity_closeout = p_continuity_sub.add_parser("closeout-packet", help="Write closeout packet yaml")
    p_continuity_closeout.add_argument("--change-id", required=True, help="Archived change id")
    p_continuity_closeout.add_argument("--closeout-statement", required=True, help="Closeout statement")
    p_continuity_closeout.add_argument("--delivered-scope", action="append", default=[], help="Delivered scope item")
    p_continuity_closeout.add_argument("--deferred-scope", action="append", default=[], help="Deferred scope item")
    p_continuity_closeout.add_argument("--key-outcome", action="append", default=[], help="Key outcome")
    p_continuity_closeout.add_argument("--unresolved-item", action="append", default=[], help="Unresolved item")
    p_continuity_closeout.add_argument("--next-direction", required=True, help="Next round default direction")
    p_continuity_closeout.add_argument("--attention-point", action="append", default=[], help="Attention point")
    p_continuity_closeout.add_argument("--carry-forward-item", action="append", default=[], help="Carry forward item")
    p_continuity_closeout.add_argument("--operator-summary", required=True, help="Operator summary")
    p_continuity_closeout.add_argument("--sponsor-summary", required=True, help="Sponsor summary")
    p_continuity_sync = p_continuity_sub.add_parser("sync-packet", help="Write sync or escalation packet yaml")
    p_continuity_sync.add_argument("--change-id", required=True, help="Target change id")
    p_continuity_sync.add_argument("--source-kind", choices=["closeout", "increment"], required=True, help="Source anchor kind")
    p_continuity_sync.add_argument("--sync-kind", choices=["routine-sync", "escalation"], required=True, help="Sync packet kind")
    p_continuity_sync.add_argument("--target-layer", required=True, help="Target layer")
    p_continuity_sync.add_argument("--target-scope", required=True, help="Target scope")
    p_continuity_sync.add_argument("--urgency", required=True, help="Urgency signal")
    p_continuity_sync.add_argument("--headline", required=True, help="Sync summary headline")
    p_continuity_sync.add_argument("--delivered-scope", action="append", default=[], help="Delivered scope item")
    p_continuity_sync.add_argument("--pending-scope", action="append", default=[], help="Pending scope item")
    p_continuity_sync.add_argument("--requested-attention", action="append", default=[], help="Requested attention item")
    p_continuity_sync.add_argument("--requested-decision", action="append", default=[], help="Requested decision item")
    p_continuity_sync.add_argument("--next-owner-suggestion", required=True, help="Suggested next owner")
    p_continuity_sync.add_argument("--next-action-suggestion", required=True, help="Suggested next action")
    p_continuity_sync_history = p_continuity_sub.add_parser("sync-history", help="Append sync packet to project history")
    p_continuity_sync_history.add_argument("--change-id", required=True, help="Target change id")
    p_continuity_sync_history.add_argument("--source-kind", choices=["closeout", "increment"], required=True, help="Source anchor kind")
    p_continuity_sync_history_months = p_continuity_sub.add_parser("sync-history-months", help="List available sync history months")
    p_continuity_sync_history_months.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_continuity_sync_history_query = p_continuity_sub.add_parser("sync-history-query", help="Read sync history with optional filters")
    month_group = p_continuity_sync_history_query.add_mutually_exclusive_group(required=True)
    month_group.add_argument("--month", help="Month key in YYYYMM")
    month_group.add_argument("--all-months", action="store_true", help="Query across all months")
    p_continuity_sync_history_query.add_argument("--change-id", default=None, help="Optional change id filter")
    p_continuity_sync_history_query.add_argument("--source-kind", choices=["closeout", "increment"], default=None, help="Optional source kind filter")
    p_continuity_sync_history_query.add_argument("--sync-kind", choices=["routine-sync", "escalation"], default=None, help="Optional sync kind filter")
    p_continuity_sync_history_query.add_argument("--summary-by", choices=["change_id", "source_kind", "sync_kind", "target_layer"], default=None, help="Optional grouped summary view")
    p_continuity_sync_history_query.add_argument("--summary-only", action="store_true", help="Return only grouped summary and hide raw event list")
    p_continuity_sync_history_query.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_continuity_export = p_continuity_sub.add_parser("export-sync-packet", help="Export sync packet to external directory")
    p_continuity_export.add_argument("--change-id", required=True, help="Target change id")
    p_continuity_export.add_argument("--source-kind", choices=["closeout", "increment"], required=True, help="Source anchor kind")
    p_continuity_export.add_argument("--output-dir", required=True, help="External export root directory")
    p_continuity_digest = p_continuity_sub.add_parser("digest", help="Read continuity and sync digest")
    p_continuity_digest.add_argument("--change-id", default=None, help="Optional explicit change id")
    p_continuity_digest.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_diag = subparsers.add_parser("diagnose-session", help="Diagnose session compression / provider drop root causes")
    p_diag.add_argument("--change-id", default=None, help="Optional target change id override")
    p_diag.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet = subparsers.add_parser("session-recovery-packet", help="Write session recovery diagnosis packet YAML")
    p_packet.add_argument("--change-id", default=None, help="Optional target change id override")
    p_packet.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet.add_argument("--output", default=None, help="Optional output yaml path")
    p_diag_alias = subparsers.add_parser("diagnose-hermes", help="Alias of diagnose-session")
    p_diag_alias.add_argument("--change-id", default=None, help="Optional target change id override")
    p_diag_alias.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet_alias = subparsers.add_parser("hermes-recovery-packet", help="Alias of session-recovery-packet")
    p_packet_alias.add_argument("--change-id", default=None, help="Optional target change id override")
    p_packet_alias.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet_alias.add_argument("--output", default=None, help="Optional output yaml path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        cmd_init(args)
    elif args.command == "version":
        return cmd_version(args)
    elif args.command in {"onboard", "setup"}:
        return cmd_onboard(args)
    elif args.command == "pilot":
        return cmd_pilot(args)
    elif args.command == "adopt":
        return cmd_adopt(args)
    elif args.command in {"hygiene", "doctor"}:
        return cmd_hygiene(args)
    elif args.command == "participants" and args.subcmd == "setup":
        return cmd_participants_setup(args)
    elif args.command == "intent" and args.subcmd == "capture":
        return cmd_intent_capture(args)
    elif args.command == "intent" and args.subcmd == "confirm":
        return cmd_intent_confirm(args)
    elif args.command == "step" and args.subcmd == "report":
        return cmd_step_report(args)
    elif args.command == "change" and args.subcmd == "create":
        cmd_change_create(args)
    elif args.command == "change" and args.subcmd == "prepare":
        return cmd_change_prepare(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "contract" and args.subcmd == "validate":
        return cmd_contract_validate(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "review":
        return cmd_review(args)
    elif args.command == "archive":
        return cmd_archive(args)
    elif args.command == "runtime-status":
        return cmd_runtime_status(args)
    elif args.command == "timeline":
        return cmd_timeline(args)
    elif args.command == "continuity" and args.subcmd == "launch-input":
        return cmd_continuity_launch_input(args)
    elif args.command == "continuity" and args.subcmd == "round-entry-summary":
        return cmd_continuity_round_entry_summary(args)
    elif args.command == "continuity" and args.subcmd == "handoff-package":
        return cmd_continuity_handoff_package(args)
    elif args.command == "continuity" and args.subcmd == "owner-transfer" and args.owner_transfer_subcmd == "prepare":
        return cmd_continuity_owner_transfer_prepare(args)
    elif args.command == "continuity" and args.subcmd == "owner-transfer" and args.owner_transfer_subcmd == "accept":
        return cmd_continuity_owner_transfer_accept(args)
    elif args.command == "continuity" and args.subcmd == "increment-package":
        return cmd_continuity_increment_package(args)
    elif args.command == "continuity" and args.subcmd == "closeout-packet":
        return cmd_continuity_closeout_packet(args)
    elif args.command == "continuity" and args.subcmd == "sync-packet":
        return cmd_continuity_sync_packet(args)
    elif args.command == "continuity" and args.subcmd == "sync-history":
        return cmd_continuity_sync_history(args)
    elif args.command == "continuity" and args.subcmd == "sync-history-months":
        return cmd_continuity_sync_history_months(args)
    elif args.command == "continuity" and args.subcmd == "sync-history-query":
        return cmd_continuity_sync_history_query(args)
    elif args.command == "continuity" and args.subcmd == "export-sync-packet":
        return cmd_continuity_export_sync_packet(args)
    elif args.command == "continuity" and args.subcmd == "digest":
        return cmd_continuity_digest(args)
    elif args.command in {"diagnose-session", "diagnose-hermes"}:
        cmd_diagnose_session(args)
    elif args.command in {"session-recovery-packet", "hermes-recovery-packet"}:
        cmd_session_recovery_packet(args)
    else:
        if args.command:
            print(
                f"Command '{args.command}' is not fully implemented in MVP. "
                "Please manipulate files in .governance/ manually for now."
            )
        else:
            parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
