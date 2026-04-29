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
    from governance.contract import ScopeConflictError

    goal = _resolve_change_prepare_goal(args.root, args.change_id, args.goal)
    if not goal.strip():
        print("--goal is required for 'ocw change prepare'.")
        print("No existing goal was found in intent-confirmation.yaml or contract.yaml.")
        return 1
    lifecycle_error = _active_change_lifecycle_error(args.root, args.change_id, getattr(args, "active_policy", None))
    if lifecycle_error:
        print(lifecycle_error)
        return 1

    try:
        payload = prepare_change_package(PrepareChangeRequest(
            root=args.root,
            change_id=args.change_id,
            title=args.title or "",
            goal=goal,
            scope_in=list(args.scope_in or []),
            scope_out=list(args.scope_out or []),
            verify_commands=list(args.verify_command or []),
            source_docs=list(args.source_doc or []),
            profile=args.profile,
        ))
    except ScopeConflictError as exc:
        print("Cannot prepare change because scope_in overlaps scope_out.")
        print("")
        print("Conflicts:")
        for conflict in exc.conflicts:
            print(f"- {conflict}")
        print("")
        print("Recommended recovery:")
        if any(conflict.startswith(".governance/** overlaps") for conflict in exc.conflicts):
            print(f"- Replace `.governance/**` with `.governance/changes/{args.change_id}/**` for change-package work.")
        print("- Keep `.governance/index/**`, `.governance/archive/**`, and `.governance/runtime/**` out of normal execution scope.")
        print("- Re-run `ocw change prepare` after narrowing scope_in.")
        return 1
    print(f"Change prepared: {payload['change_id']}")
    print("")
    print(_format_agent_handoff(payload["change_id"]))
    return 0


def _resolve_change_prepare_goal(root: str | Path, change_id: str, explicit_goal: str) -> str:
    if (explicit_goal or "").strip():
        return explicit_goal.strip()
    from governance.change_package import read_change_package
    from governance.simple_yaml import load_yaml

    try:
        package = read_change_package(root, change_id)
    except Exception:
        return ""
    for filename, keys in (
        ("intent-confirmation.yaml", ("project_intent",)),
        ("contract.yaml", ("objective",)),
    ):
        path = package.path / filename
        if not path.exists():
            continue
        payload = load_yaml(path)
        for key in keys:
            value = str(payload.get(key) or "").strip()
            if value:
                return value
    return ""


def _format_agent_handoff(change_id: str) -> str:
    return "\n".join([
        "Agent-first handoff ready.",
        "Read these files before continuing:",
        "- .governance/AGENTS.md",
        "- .governance/local/current-state.md",
        "- .governance/agent-playbook.md",
        f"- .governance/changes/{change_id}/contract.yaml",
        f"- .governance/changes/{change_id}/bindings.yaml",
        "",
        "Human control baseline before Step 6:",
        f"- ocw --root . participants setup --profile personal --change-id {change_id}",
        f"- ocw --root . step report --change-id {change_id} --step 1 --format human",
        f"- ocw --root . intent capture --change-id {change_id} --project-intent \"Describe the real iteration intent\"",
        f"- ocw --root . intent confirm --change-id {change_id} --confirmed-by human-sponsor",
        f"- Step 5 approval is required before Step 6 execution.",
        f"- Step 8 review decision and approval trace are required before archive.",
        f"- Step 9 human approval is required before archive is finalized.",
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
    cmd_init(argparse.Namespace(root=str(target), legacy_layout=False))
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
    from governance.simple_yaml import load_yaml

    try:
        contract_path = Path(args.path) if args.path else read_change_package(args.root, args.change_id).path / "contract.yaml"
        contract = load_contract(contract_path)
        change_id = args.change_id or contract_path.parent.name
        drift = _intent_contract_scope_drift(contract_path, contract)
        if drift:
            raise ContractValidationError(drift)
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


def _intent_contract_scope_drift(contract_path: Path, contract: dict) -> str | None:
    intent_path = contract_path.parent / "intent-confirmation.yaml"
    if not intent_path.exists():
        return None
    from governance.simple_yaml import load_yaml

    intent = load_yaml(intent_path)
    if intent.get("status") != "confirmed":
        return None
    intent_scope = set(intent.get("scope_in", []))
    if not intent_scope:
        return None
    contract_scope = set(contract.get("scope_in", []))
    evidence_scope = f".governance/changes/{contract.get('change_id')}/evidence/**"
    contract_scope.discard(evidence_scope)
    if intent_scope != contract_scope:
        return (
            "intent scope differs from contract scope: "
            f"intent scope_in={sorted(intent_scope)} contract scope_in={sorted(contract_scope)}"
        )
    return None


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
    from governance.step_report import materialize_step_report
    materialize_step_report(args.root, change_id=package.change_id, step=6)
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
    print(f"- Step 6 report: .governance/changes/{package.change_id}/step-reports/step-6.md")
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
    print("")
    print("Human control baseline next actions:")
    for item in payload.get("human_control_baseline_next_actions", []):
        print(f"- {item}")
    return 0


def cmd_activate(args):
    from governance.activation import build_project_activation, format_project_activation

    payload = build_project_activation(args.root, change_id=args.change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(format_project_activation(payload), end="")
    return 0


def cmd_resume(args):
    from governance.activation import build_project_activation, format_project_activation

    payload = build_project_activation(args.root, change_id=args.change_id, list_only=args.list)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(format_project_activation(payload), end="")
    return 0


def cmd_profile(args):
    from governance.profiles import apply_adoption_profile, get_adoption_profile, list_adoption_profiles

    if args.profile_subcmd == "list":
        profiles = list_adoption_profiles()
        if args.format == "json":
            from governance.profiles import ADOPTION_ADD_ONS

            print(json.dumps({"profiles": profiles, "agent_selected_add_ons": list(ADOPTION_ADD_ONS.values())}, ensure_ascii=False, indent=2))
            return 0
        for item in profiles:
            print(f"- {item['profile_id']}: {item['human_label']} - {item['description']}")
        print("Agent-selected add-ons:")
        print("- large-reference-set: 大量资料阅读模式 - 可叠加，不是单独协作档位")
        return 0
    if args.profile_subcmd == "show":
        try:
            profile = get_adoption_profile(args.profile_id)
        except ValueError as exc:
            print(str(exc))
            return 1
        if args.format == "json":
            print(json.dumps(profile, ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(profile), end="")
            return 0
        print(f"{profile['profile_id']}: {profile['display_name']}")
        print(f"Human label: {profile['human_label']}")
        print(profile["description"])
        print(f"Selection: {profile['selection_guidance']}")
        return 0
    if args.profile_subcmd == "apply":
        try:
            result = apply_adoption_profile(args.root, args.profile_id, agent_id=args.agent_id, preview=args.preview, force=args.force)
        except ValueError as exc:
            print(str(exc))
            return 1
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if result.get("preview"):
            print(f"Profile apply preview: {result['profile_id']}")
            print(f"- would_overwrite: {str(result.get('would_overwrite')).lower()}")
            print(f"- requires_force: {str(result.get('requires_force')).lower()}")
            return 0
        print(f"Applied adoption profile: {result['profile_id']}")
        print(f"- path: {result['path']}")
        print(f"- participant_profile_dir: {result['participant_profile_dir']}")
        return 0
    return 0


def cmd_context_pack(args):
    from governance.context_pack import create_context_pack, read_context_pack

    if args.context_pack_subcmd == "create":
        result = create_context_pack(args.root, args.change_id, level=args.level)
        print("Context pack created")
        print(f"- context_pack: {result['context_pack']}")
        print(f"- context_pack_md: {result['context_pack_md']}")
        return 0
    if args.context_pack_subcmd == "read":
        pack = read_context_pack(args.root, args.change_id, level=args.level)
        if args.format == "json":
            print(json.dumps(pack, ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(pack), end="")
            return 0
        print(f"Context pack: {pack.get('change_id')}")
        for item in pack.get("authoritative_reads", []):
            print(f"- {item}")
        return 0
    return 0


def cmd_handoff(args):
    from governance.context_pack import write_compact_handoff

    if not args.compact:
        print("Only compact handoff is supported: use --compact.")
        return 1
    result = write_compact_handoff(args.root, args.change_id)
    print("Compact handoff written")
    print(f"- handoff: {result['handoff']}")
    print(f"- context_pack: {result['context_pack']}")
    return 0


def cmd_runtime(args):
    from governance.runtime_profiles import add_runtime_profile, list_runtime_profiles, show_runtime_profile

    if args.runtime_subcmd == "profile" and args.profile_action == "add":
        try:
            payload = add_runtime_profile(
                args.root,
                runtime_id=args.runtime_id,
                runtime_type=args.runtime_type,
                owner=args.owner,
                capabilities=list(args.capability or []),
                risks=list(args.risk or []),
                evidence=list(args.evidence or []),
                constraints=list(args.constraint or []),
            )
        except ValueError as exc:
            print(str(exc))
            return 1
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(payload), end="")
            return 0
        print(f"Runtime profile written: {payload['runtime_id']}")
        print(f"- authority: {payload['authority']}")
        return 0
    if args.runtime_subcmd == "profile" and args.profile_action == "list":
        payload = {"profiles": list_runtime_profiles(args.root)}
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(payload), end="")
            return 0
        for item in payload["profiles"]:
            print(f"- {item['runtime_id']}: {item.get('runtime_type')} owner={item.get('owner')}")
        return 0
    if args.runtime_subcmd == "profile" and args.profile_action == "show":
        try:
            payload = show_runtime_profile(args.root, args.runtime_id)
        except ValueError as exc:
            print(str(exc))
            return 1
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(payload), end="")
            return 0
        print(f"Runtime profile: {payload['runtime_id']}")
        print(f"- type: {payload.get('runtime_type')}")
        print(f"- owner: {payload.get('owner')}")
        return 0
    return 0


def cmd_runtime_event(args):
    from governance.runtime_events import append_change_runtime_event

    event = append_change_runtime_event(
        args.root,
        change_id=args.change_id,
        event_type=args.event_type,
        step=args.step,
        actor_id=args.actor_id,
        refs=list(args.ref or []),
        authority=args.authority,
    )
    if args.format == "json":
        print(json.dumps(event, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(event), end="")
        return 0
    print(f"Runtime event appended: {event['event_id']}")
    print(f"- ref: .governance/changes/{args.change_id}/evidence/runtime-events/events.yaml")
    return 0


def cmd_adapter(args):
    from governance.evidence import validate_adapter_output
    from governance.simple_yaml import load_yaml

    payload = load_yaml(args.path)
    errors = validate_adapter_output(payload)
    result = {"schema": "adapter-validation/v1", "status": "pass" if not errors else "fail", "errors": errors}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(result), end="")
        return 0 if not errors else 1
    print(f"Adapter output validation: {result['status']}")
    for error in errors:
        print(f"- {error}")
    return 0 if not errors else 1


def cmd_evidence(args):
    if args.evidence_subcmd == "add":
        from governance.lean_commands import add_evidence

        entry = add_evidence(
            args.root,
            evidence_id=args.id,
            kind=args.kind,
            ref=args.ref,
            summary=args.summary,
            created_by=args.created_by,
            round_id=args.round_id,
        )
        print(f"Lean evidence added: {entry['evidence_id']}")
        return 0

    from governance.evidence import validate_adapter_output, write_evidence_index
    from governance.simple_yaml import load_yaml

    if args.evidence_subcmd == "index":
        path = write_evidence_index(Path(args.root) / ".governance" / "changes" / args.change_id / "evidence")
        print(f"Evidence index written: {Path(path).relative_to(Path(args.root))}")
        return 0
    if args.evidence_subcmd == "append":
        payload = load_yaml(args.adapter)
        errors = validate_adapter_output(payload)
        if errors:
            print("Evidence append failed: adapter output is invalid")
            for error in errors:
                print(f"- {error}")
            return 1
        target_dir = Path(args.root) / ".governance" / "changes" / args.change_id / "evidence"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "adapter-output.yaml"
        from governance.simple_yaml import write_yaml

        write_yaml(target, payload)
        write_evidence_index(target_dir)
        print(f"Evidence appended from adapter: {target.relative_to(Path(args.root))}")
        return 0
    return 0


def cmd_round(args):
    from governance.lean_commands import approve_round_gate, close_round, init_participants, start_round

    if args.round_subcmd == "start":
        state = start_round(
            args.root,
            round_id=args.round_id,
            goal=args.goal,
            scope_in=args.scope_in,
            scope_out=args.scope_out,
            acceptance_summary=args.acceptance,
        )
        print(f"Lean round started: {state['active_round']['round_id']}")
        return 0
    if args.round_subcmd == "participants" and args.participants_subcmd == "init":
        state = init_participants(
            args.root,
            sponsor=args.sponsor,
            owner_agent=args.owner_agent,
            orchestrator=args.orchestrator,
            executor=args.executor,
            reviewer=args.reviewer,
            advisors=args.advisor,
        )
        status = state["active_round"]["participant_initialization"]["status"]
        print(f"Lean participants initialized: {status}")
        return 0 if status == "complete" else 1
    if args.round_subcmd == "approve":
        state = approve_round_gate(
            args.root,
            gate=args.gate,
            approved_by=args.approved_by,
            evidence_ref=args.evidence_ref,
            reason=args.reason,
        )
        print(f"Lean gate approved: {args.gate} by {state['active_round']['gates'][args.gate]['approved_by']}")
        return 0
    if args.round_subcmd == "close":
        ok, payload = close_round(
            args.root,
            final_status=args.final_status,
            closed_by=args.closed_by,
            summary=args.summary,
            evidence_ref=args.evidence_ref,
        )
        if not ok:
            print(f"Lean round close blocked: {payload['reason']}")
            return 1
        print(f"Lean round closed: {payload['round_id']} ({payload['final_status']})")
        return 0
    print("Unsupported round command.")
    return 1


def cmd_rule(args):
    from governance.lean_commands import add_rule, update_rule_status

    if args.rule_subcmd == "add":
        ok, payload = add_rule(
            args.root,
            rule_id=args.id,
            name=args.name,
            kind=args.kind,
            failure_impact=args.failure_impact,
            applies_to=args.applies_to,
            command=args.rule_command,
            authorization_ref=args.authorization_ref,
        )
        if not ok:
            print(f"Rule add blocked: {payload['reason']}")
            return 1
        print(f"Lean rule added: {payload['id']}")
        return 0
    status_by_subcmd = {"suspend": "suspended", "resume": "active", "remove": "removed"}
    if args.rule_subcmd in status_by_subcmd:
        ok, payload = update_rule_status(
            args.root,
            rule_id=args.id,
            status=status_by_subcmd[args.rule_subcmd],
            actor=args.actor,
            reason=args.reason,
            authorization_ref=args.authorization_ref,
        )
        if not ok:
            print(f"Rule change blocked: {payload['reason']}")
            return 1
        print(f"Lean rule {args.rule_subcmd}: {payload['id']}")
        return 0
    print("Unsupported rule command.")
    return 1


def cmd_index_rebuild(args):
    from governance.index import rebuild_governance_index

    payload = rebuild_governance_index(args.root)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print("Index rebuilt")
    print(f"- changes_count: {payload['changes_count']}")
    print(f"- active_count: {payload['active_count']}")
    print(f"- archive_count: {payload['archive_count']}")
    print(f"- changes_index: {payload['changes_index']}")
    print(f"- active_changes: {payload['active_changes']}")
    print(f"- archive_map: {payload['archive_map']}")
    return 0


def cmd_hygiene(args):
    if getattr(args, "cleanup", False):
        from governance.lean_migration import cleanup_legacy

        payload = cleanup_legacy(args.root, dry_run=getattr(args, "dry_run", False), confirm=getattr(args, "confirm", False))
        if payload.get("blocked"):
            print("清理需要显式确认：请使用 --confirm，或先用 --dry-run 查看计划。")
            return 1
        if payload.get("dry_run"):
            print("清理预览")
        else:
            print("清理确认已记录，未执行物理删除")
        print("")
        for item in payload.get("candidates", []):
            print(f"- {item}")
        if payload.get("receipt"):
            print(f"- receipt: {payload['receipt']}")
        return 0

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


def cmd_migrate(args):
    from governance.lean_migration import detect_legacy_layout, migrate_legacy_to_lean, verify_migration

    if args.subcmd == "detect":
        payload = detect_legacy_layout(args.root)
        print("旧版治理目录检测")
        print("")
        print(f"- layout: {payload['layout']}")
        print(f"- protocol_version: {payload['protocol_version']}")
        print(f"- active_legacy_change: {payload['active_legacy_change']}")
        print("- legacy_dirs:")
        for name, meta in payload["legacy_dirs"].items():
            print(f"  - {name}: exists={str(meta['exists']).lower()} entries={meta['entry_count']}")
        print("- cleanup_candidates:")
        for item in payload["cleanup_candidates"]:
            print(f"  - {item}")
        return 0
    if args.subcmd == "lean":
        dry_run = bool(args.dry_run or not args.confirm)
        payload = migrate_legacy_to_lean(args.root, dry_run=dry_run, confirm=args.confirm)
        if payload.get("blocked"):
            print("迁移需要显式确认：请使用 --confirm，或先用 --dry-run 查看计划。")
            return 1
        if payload["dry_run"]:
            print("迁移预览")
        else:
            print("迁移完成")
        print("")
        for item in payload.get("move_plan", []):
            print(f"- {item['from']} -> {item['to']}")
        if payload.get("receipt"):
            print(f"- receipt: {payload['receipt']}")
        return 0
    if args.subcmd == "verify":
        payload = verify_migration(args.root)
        if payload["ok"]:
            print("迁移验证通过")
            return 0
        print("迁移验证失败")
        for error in payload["errors"]:
            print(f"- {error}")
        return 1
    return 1


def cmd_uninstall(args):
    from governance.lean_migration import uninstall_governance

    payload = uninstall_governance(args.root, dry_run=args.dry_run or not args.confirm, confirm=args.confirm)
    if payload.get("blocked"):
        print("卸载需要显式确认：请使用 --confirm，或先用 --dry-run 查看计划。")
        return 1
    if payload["dry_run"]:
        print("卸载预览")
    else:
        print("卸载完成")
    print("")
    for item in payload.get("targets", []):
        print(f"- {item}")
    if payload.get("receipt"):
        print(f"- receipt: {payload['receipt']}")
    return 0


def cmd_participants_setup(args):
    from governance.participants import setup_participants_profile

    payload = setup_participants_profile(
        args.root,
        profile=args.profile,
        participant_specs=list(args.participant or []),
        step_owner_specs=list(args.step_owner or []),
        step_assistant_specs=list(args.step_assistant or []),
        step_reviewer_specs=list(args.step_reviewer or []),
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
    for warning in payload.get("warnings", []):
        print(f"- warning: {warning}")
    return 0


def cmd_participants_list(args):
    from governance.status_views import participants_list, render_participants_list

    payload = participants_list(args.root, args.change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(render_participants_list(payload), end="")
    return 0


def _print_structured(payload: dict, fmt: str, text: str) -> int:
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if fmt == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


def cmd_team(args):
    from governance.team_loop import format_team_digest, format_team_status, team_digest, team_status

    if args.subcmd == "status":
        payload = team_status(args.root)
        return _print_structured(payload, args.format, format_team_status(payload))
    if args.subcmd == "digest":
        payload = team_digest(args.root, period=args.period)
        return _print_structured(payload, args.format, format_team_digest(payload))
    return 1


def cmd_participant(args):
    from governance.team_loop import (
        assignment_set,
        format_item_list,
        participant_assign,
        participant_discover,
        participant_list,
        participant_register,
        participant_update,
    )

    try:
        if args.subcmd == "discover":
            payload = participant_discover(args.root, recorded_by=args.recorded_by)
            return _print_structured(payload, args.format, format_item_list("Participant candidates", payload.get("discovered_candidates", [])))
        if args.subcmd == "register":
            payload = participant_register(
                args.root,
                participant_id=args.participant_id,
                participant_type=args.type,
                domain=args.domain,
                entrypoint=args.entrypoint,
                capability=list(args.capability or []),
                default_role=list(args.default_role or []),
                step=list(args.step or []),
                recorded_by=args.recorded_by,
                remote=args.remote,
            )
            return _print_structured(payload, args.format, format_item_list("Participants", payload.get("participants", [])))
        if args.subcmd == "list":
            payload = participant_list(args.root)
            return _print_structured(payload, args.format, format_item_list("Participants", payload.get("participants", [])))
        if args.subcmd == "assign":
            payload = participant_assign(
                args.root,
                change_id=args.change_id,
                step=args.step,
                role=args.role,
                actor=args.participant_id,
                recorded_by=args.recorded_by,
                note=args.note or "",
            )
            return _print_structured(payload, args.format, format_item_list("Assignments", payload.get("assignments", [])))
        if args.subcmd == "update":
            updates = {
                "domain": args.domain,
                "entrypoint": args.entrypoint,
                "capabilities": list(args.capability or []),
                "default_roles": list(args.default_role or []),
                "eligible_steps": list(args.step or []),
                "remote": args.remote if args.remote else None,
            }
            payload = participant_update(args.root, participant_id=args.participant_id, updates=updates, recorded_by=args.recorded_by)
            return _print_structured(payload, args.format, format_item_list("Participants", payload.get("participants", [])))
    except ValueError as exc:
        print(f"Participant command failed: {exc}")
        return 1
    return 1


def cmd_assignment(args):
    from governance.team_loop import assignment_set, format_item_list

    try:
        payload = assignment_set(
            args.root,
            change_id=args.change_id,
            step=args.step,
            role=args.role,
            actor=args.actor,
            recorded_by=args.recorded_by,
            note=args.note or "",
        )
    except ValueError as exc:
        print(f"Assignment failed: {exc}")
        return 1
    return _print_structured(payload, args.format, format_item_list("Assignments", payload.get("assignments", [])))


def cmd_blocked(args):
    from governance.team_loop import blocked_clear, blocked_set, format_item_list

    try:
        if args.subcmd == "set":
            payload = blocked_set(
                args.root,
                change_id=args.change_id,
                reason=args.reason,
                waiting_on=args.waiting_on,
                next_decision=args.next_decision,
                recorded_by=args.recorded_by,
            )
        elif args.subcmd == "clear":
            payload = blocked_clear(args.root, block_id=args.block_id, recorded_by=args.recorded_by, resolution=args.resolution or "")
        else:
            return 1
    except ValueError as exc:
        print(f"Blocked command failed: {exc}")
        return 1
    return _print_structured(payload, args.format, format_item_list("Blocked", payload.get("blocks", [])))


def cmd_reviewer(args):
    from governance.team_loop import format_item_list, reviewer_queue

    try:
        payload = reviewer_queue(
            args.root,
            change_id=args.change_id,
            reviewer=args.reviewer or "",
            priority=args.priority,
            recorded_by=args.recorded_by or "",
        )
    except ValueError as exc:
        print(f"Reviewer queue failed: {exc}")
        return 1
    return _print_structured(payload, args.format, format_item_list("Reviewer queue", payload.get("queue", []), id_key="change_id"))


def cmd_recurring_intent(args):
    from governance.team_loop import format_item_list, recurring_intent_add, recurring_intent_trigger

    try:
        if args.subcmd == "add":
            payload = recurring_intent_add(args.root, intent_id=args.intent_id, summary=args.summary, cadence=args.cadence, recorded_by=args.recorded_by)
            return _print_structured(payload, args.format, format_item_list("Recurring intents", payload.get("intents", [])))
        if args.subcmd == "trigger":
            payload = recurring_intent_trigger(args.root, intent_id=args.intent_id, change_id=args.change_id, recorded_by=args.recorded_by)
            return _print_structured(payload, args.format, f"Recurring intent triggered: {payload['intent_id']} -> {payload['change_id']}\n- current_step: {payload['current_step']}\n- status: {payload['status']}\n")
    except ValueError as exc:
        print(f"Recurring intent failed: {exc}")
        return 1
    return 1


def cmd_carry_forward(args):
    from governance.team_loop import carry_forward_add, carry_forward_list, carry_forward_promote, format_item_list

    try:
        if args.subcmd == "add":
            payload = carry_forward_add(args.root, item_id=args.item_id, summary=args.summary, source_change_id=args.source_change_id, recorded_by=args.recorded_by)
        elif args.subcmd == "list":
            payload = carry_forward_list(args.root)
        elif args.subcmd == "promote":
            payload = carry_forward_promote(args.root, item_id=args.item_id, change_id=args.change_id, recorded_by=args.recorded_by)
        else:
            return 1
    except ValueError as exc:
        print(f"Carry-forward failed: {exc}")
        return 1
    return _print_structured(payload, args.format, format_item_list("Carry-forward", payload.get("items", [])))


def cmd_retrospective(args):
    from governance.team_loop import format_item_list, retrospective_add, retrospective_list

    if args.subcmd == "add":
        payload = retrospective_add(
            args.root,
            retrospective_id=args.retrospective_id,
            change_id=args.change_id,
            summary=args.summary,
            learning=list(args.learning or []),
            recorded_by=args.recorded_by,
        )
        return _print_structured(payload, args.format, f"Retrospective recorded: {payload['id']}\n- change_id: {payload['change_id']}\n")
    if args.subcmd == "list":
        payload = retrospective_list(args.root)
        return _print_structured(payload, args.format, format_item_list("Retrospectives", payload.get("retrospectives", [])))
    return 1


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
    print(f"- Step 1 report: .governance/changes/{args.change_id}/step-reports/step-1.md")
    if payload.get("status") == "confirmed":
        print(f"- Step 2 report: .governance/changes/{args.change_id}/step-reports/step-2.md")
    else:
        print("- Next: confirm Step 1 before generating future step reports.")
    return 0


def cmd_intent_confirm(args):
    from governance.intent import confirm_intent

    payload = confirm_intent(args.root, change_id=args.change_id, confirmed_by=args.confirmed_by, note=args.note or "")
    from governance.human_gates import record_intent_confirmation_approval

    record_intent_confirmation_approval(
        args.root,
        change_id=args.change_id,
        confirmed_by=args.confirmed_by,
        note=args.note or "",
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"Intent confirmed: {payload['change_id']}")
    print(f"- confirmed_by: {payload['human_confirmation']['confirmed_by']}")
    print(f"- ref: .governance/changes/{args.change_id}/intent-confirmation.yaml")
    print(f"- Step 1 approval source: .governance/changes/{args.change_id}/human-gates.yaml#approvals.1")
    return 0


def cmd_intent_status(args):
    from governance.status_views import intent_status, render_intent_status

    payload = intent_status(args.root, args.change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(render_intent_status(payload), end="")
    return 0


def cmd_change_status(args):
    from governance.status_views import change_status, render_change_status

    change_id = args.change_id_flag or args.change_id
    if not change_id:
        print("--change-id is required for 'ocw change status'.")
        return 1
    payload = change_status(args.root, change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    print(render_change_status(payload), end="")
    return 0


def cmd_preflight(args):
    from governance.preflight import (
        check_execution_preflight,
        format_execution_preflight,
        record_flow_bypass_recovery,
    )

    if args.subcmd == "check":
        payload = check_execution_preflight(args.root, args.change_id, list(args.path or []))
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(payload), end="")
        else:
            print(format_execution_preflight(payload), end="")
        return 0 if payload.get("can_execute") else 1
    if args.subcmd == "recovery":
        payload = record_flow_bypass_recovery(
            args.root,
            change_id=args.change_id,
            reason=args.reason,
            modified_files=list(args.modified or []),
            missing_items=list(args.missing or []),
            recovery_actions=list(args.action or []),
            recorded_by=args.recorded_by,
        )
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif args.format == "yaml":
            from governance.simple_yaml import dump_yaml

            print(dump_yaml(payload), end="")
        else:
            print(f"Flow bypass recovery recorded: {args.change_id}")
            print(f"- ref: .governance/changes/{args.change_id}/recovery/bypass-records.yaml")
            print("- classification: flow_bypass_recovery")
            print("- normal_evidence: false")
        return 0
    return 1


def cmd_audit(args):
    from governance.audit import format_governance_audit, run_governance_audit

    payload = run_governance_audit(args.root, args.change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
    else:
        print(format_governance_audit(payload), end="")
    return 1 if payload.get("status") == "fail" else 0


def cmd_step_report(args):
    from governance.contract import ContractValidationError
    from governance.step_report import materialize_step_report

    try:
        payload = materialize_step_report(args.root, change_id=args.change_id, step=args.step)
    except ContractValidationError as exc:
        print(f"Step report failed: contract is not ready for change '{args.change_id}'.")
        print("Next action: run 'ocw change prepare' or complete contract.yaml before requesting a step report.")
        print(f"Detail: {exc}")
        return 1
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.format == "yaml":
        from governance.simple_yaml import dump_yaml

        print(dump_yaml(payload), end="")
        return 0
    if args.format == "human":
        print(f"# {payload['standard_step']}")
        print("")
        print(f"- traditional_mapping: {payload['traditional_mapping']}")
        print(f"- owner: {payload['owner']}")
        print(f"- reviewer: {payload.get('reviewer') or 'none'}")
        print(f"- gate_type: {payload['gate_type']}")
        print(f"- gate_state: {payload['gate_state']}")
        print(f"- approval_state: {payload['approval_state']}")
        print("")
        print("## Inputs")
        for item in payload["inputs"]:
            print(f"- {item}")
        print("")
        print("## Outputs")
        for item in payload["outputs"]:
            print(f"- {item}")
        print("")
        print("## Intent summary")
        _print_mapping(payload.get("intent_summary", {}))
        print("")
        print("## Artifact summary")
        _print_mapping(payload.get("artifact_summary", {}))
        print("")
        print("## Review gate vs decision")
        _print_mapping(payload.get("review_gate_vs_decision", {}))
        print("")
        print("## Evidence")
        _print_evidence(payload.get("evidence", []))
        print("")
        print("## Done criteria")
        for item in payload["done_criteria"]:
            print(f"- {item}")
        print("")
        print("## framework_controls")
        for item in payload["framework_controls"]:
            print(f"- {item}")
        print("")
        print("## agent_actions_done")
        for item in payload["agent_actions_done"]:
            print(f"- {item}")
        print("")
        print("## agent_actions_expected")
        for item in payload["agent_actions_expected"]:
            print(f"- {item}")
        print("")
        print("## Human confirmation options")
        if payload["human_confirmation_options"]:
            for item in payload["human_confirmation_options"]:
                print(f"- {item['action']}: {item['label']}")
        else:
            print("- none")
        print("")
        print(f"Recommended next action: {payload['recommended_next_action']}")
        return 0
    print(f"Step report written: .governance/changes/{args.change_id}/step-reports/step-{payload['step']}.md")
    print(f"- owner: {payload['owner']}")
    print(f"- human_gate: {str(payload['human_gate']).lower()}")
    print(f"- recommended_next_action: {payload['recommended_next_action']}")
    print("")
    print("Inputs:")
    for item in payload["inputs"]:
        print(f"- {item}")
    print("Outputs:")
    for item in payload["outputs"]:
        print(f"- {item}")
    print("Done criteria:")
    for item in payload["done_criteria"]:
        print(f"- {item}")
    print("Participant responsibilities:")
    for item in payload["participant_responsibilities"]:
        print(f"- {item}")
    return 0


def _print_mapping(payload: dict) -> None:
    if not payload:
        print("- none")
        return
    for key, value in payload.items():
        if isinstance(value, list):
            print(f"- {key}:")
            if value:
                for item in value:
                    print(f"  - {item}")
            else:
                print("  - none")
        else:
            print(f"- {key}: {value}")


def _print_evidence(items: list[dict]) -> None:
    if not items:
        print("- none")
        return
    for item in items:
        print(f"- {item.get('kind')}:")
        for key, value in item.items():
            if key == "kind":
                continue
            if isinstance(value, list):
                print(f"  - {key}:")
                if value:
                    for entry in value:
                        print(f"    - {entry}")
                else:
                    print("    - none")
            elif isinstance(value, dict):
                print(f"  - {key}:")
                if value:
                    for nested_key, nested_value in value.items():
                        print(f"    - {nested_key}: {nested_value}")
                else:
                    print("    - none")
            else:
                print(f"  - {key}: {value}")


def cmd_step_approve(args):
    from governance.human_gates import approve_step

    try:
        payload = approve_step(
            args.root,
            change_id=args.change_id,
            step=args.step,
            approved_by=args.approved_by,
            note=args.note or "",
            recorded_by=args.recorded_by or "",
            evidence_ref=args.evidence_ref or "",
            approval_token=args.approval_token or "",
        )
    except ValueError as exc:
        print(f"Step approval failed: {exc}")
        return 1
    if args.step == 5:
        _mark_step5_approved_for_step6(args.root, args.change_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    approvals = payload.get("approvals", {})
    approval = approvals.get(args.step) or approvals.get(str(args.step))
    if not approval:
        acknowledgements = payload.get("acknowledgements", [])
        latest = acknowledgements[-1] if acknowledgements else {}
        print(f"Step {args.step} acknowledged: {args.change_id}")
        print(f"- acknowledged_by: {latest.get('acknowledged_by')}")
        print(f"- ref: .governance/changes/{args.change_id}/human-gates.yaml#acknowledgements")
        return 0
    print(f"Step {args.step} approved: {args.change_id}")
    print(f"- approved_by: {approval['approved_by']}")
    print(f"- ref: .governance/changes/{args.change_id}/human-gates.yaml")
    return 0


def _mark_step5_approved_for_step6(root: str | Path, change_id: str) -> None:
    from governance.change_package import read_change_package, update_manifest
    from governance.index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
    from governance.simple_yaml import load_yaml

    package = read_change_package(root, change_id)
    readiness = dict(package.manifest.get("readiness") or {})
    readiness["step6_entry_ready"] = True
    readiness["missing_items"] = [
        item for item in readiness.get("missing_items", [])
        if item not in {"intent_confirmation", "step1_confirmation", "step5_approval", "step5_confirmation"}
    ]
    updates = {"status": "step6-in-progress", "current_step": 6, "readiness": readiness}
    contract_path = package.path / "contract.yaml"
    if contract_path.exists():
        contract = load_yaml(contract_path)
        validation_objects = list(contract.get("validation_objects", []))
        if validation_objects:
            updates["target_validation_objects"] = validation_objects
    manifest = update_manifest(root, change_id, **updates)
    current = read_current_change(root).get("current_change") or {}
    entry = {
        **current,
        "change_id": change_id,
        "path": str(package.path.relative_to(Path(root))),
        "status": manifest.get("status"),
        "current_step": manifest.get("current_step"),
        "title": manifest.get("title"),
    }
    set_current_change(root, entry)
    upsert_change_entry(root, entry)
    set_maintenance_status(root, status=manifest.get("status"), current_change_active=manifest.get("status"), current_change_id=change_id)
    from governance.step_report import materialize_step_report
    for step in range(1, 6):
        materialize_step_report(root, change_id=change_id, step=step)


def cmd_verify(args):
    from governance.verify import write_verify_result
    from governance.runtime_events import append_runtime_event

    try:
        payload = write_verify_result(
            args.root,
            args.change_id,
            run_commands=args.run_commands,
            timeout_seconds=args.timeout_seconds,
        )
        from governance.step_report import materialize_step_report
        materialize_step_report(args.root, change_id=args.change_id, step=7)
        print(f"Verify recorded: {payload['change_id']} -> {payload['summary']['status']}")
        print(f"- product_verification: {payload.get('product_verification', {}).get('mode')}")
        print(f"- Step 7 report: .governance/changes/{args.change_id}/step-reports/step-7.md")
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
            allow_reviewer_mismatch=args.allow_reviewer_mismatch,
            bypass_reason=args.bypass_reason or "",
            bypass_recorded_by=args.bypass_recorded_by or "",
            bypass_evidence_ref=args.bypass_evidence_ref or "",
            runtime=args.runtime or "",
            health_check=args.health_check or "",
            invocation_status=args.invocation_status or "",
            failure_reason=args.failure_reason or "",
            fallback_reviewer=args.fallback_reviewer or "",
            review_artifact_ref=args.review_artifact_ref or "",
        )
        status_label = {
            "approve": "review-approved",
            "reject": "review-rejected",
            "revise": "review-revise",
        }.get(payload["decision"]["status"], payload["decision"]["status"])
        print(f"Review recorded: {payload['change_id']} -> {status_label}")
        for warning in payload.get("warnings", []):
            print(f"- warning: {warning}")
            if args.allow_reviewer_mismatch:
                print("- reviewer mismatch allowed; audit bypass recorded in human-gates.yaml")
        from governance.step_report import materialize_step_report
        materialize_step_report(args.root, change_id=args.change_id, step=8)
        print(f"- Step 8 report: .governance/changes/{args.change_id}/step-reports/step-8.md")
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


def cmd_review_invocation(args):
    from governance.review_invocation import record_review_invocation

    try:
        payload = record_review_invocation(
            args.root,
            change_id=args.change_id,
            status=args.status,
            reviewer=args.reviewer,
            runtime=args.runtime or "",
            note=args.note or "",
            timeout_policy=args.timeout_policy or "",
            artifact_ref=args.artifact_ref or "",
        )
        from governance.step_report import materialize_step_report

        materialize_step_report(args.root, change_id=args.change_id, step=8)
    except Exception as exc:
        print(f"Review invocation failed: {exc}")
        return 1
    print(f"Review invocation recorded: {payload['change_id']} -> {payload['status']}")
    print(f"- last_heartbeat_at: {payload.get('last_heartbeat_at')}")
    print(f"- ref: .governance/changes/{args.change_id}/review-invocation.yaml")
    print(f"- Step 8 report: .governance/changes/{args.change_id}/step-reports/step-8.md")
    return 0


def cmd_archive(args):
    from governance.archive import archive_change
    from governance.audit import format_governance_audit, run_governance_audit
    from governance.runtime_events import append_runtime_event

    try:
        audit = run_governance_audit(args.root, args.change_id)
        if audit.get("status") == "fail":
            print("Archive failed: governance audit did not pass")
            print(format_governance_audit(audit), end="")
            return 1
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


def cmd_revise(args):
    from governance.revision import open_revision
    from governance.runtime_events import append_runtime_event

    try:
        payload = open_revision(args.root, args.change_id, reason=args.reason, recorded_by=args.recorded_by)
        append_runtime_event(
            args.root,
            change_id=args.change_id,
            event_type="revision_opened",
            step=6,
            from_status="review-revise",
            to_status="revision-open",
            actor_id=args.recorded_by,
            refs=[payload["history_ref"]],
        )
        print(f"Revision opened: {payload['change_id']} round={payload['revision']['revision_round']}")
        print(f"- status: {payload['status']}")
        print(f"- ref: {payload['history_ref']}")
        return 0
    except Exception as exc:
        print(f"Revision failed: {exc}")
        return 1


def cmd_init(args):
    if getattr(args, "legacy_layout", False):
        from governance.index import ensure_governance_index

        ensure_governance_index(args.root)
        print(f"Initialized open-cowork governance in {args.root}/.governance (legacy layout)")
        return 0
    from governance.lean_paths import ensure_lean_layout

    ensure_lean_layout(args.root)
    print(f"Initialized open-cowork v0.3.11 lean governance in {args.root}/.governance")
    return 0


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
    cmd_init(argparse.Namespace(root=str(target), legacy_layout=False))
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
        "- After a change exists, start with Step 1 input framing; do not treat prepare as Step 5 completion.",
        "- Step 5 approval is required before Step 6 execution.",
        "- Step 8 review decision and approval trace are required before archive.",
        "- Step 9 human approval is required before archive is finalized.",
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
        if _should_render_lean_status(args):
            _print_lean_status(args.root)
            return
        if getattr(args, "sync_current_state", False):
            from governance.current_state import sync_current_state

            path = sync_current_state(args.root)
            print(f"Current state synced: {path}")
            return
        if getattr(args, "last_archive", False):
            from governance.status_views import last_archive_summary, render_last_archive_summary

            print(render_last_archive_summary(last_archive_summary(args.root)), end="")
            return
        if getattr(args, "change_id", None):
            from governance.step_matrix import format_status_snapshot_view, write_status_snapshot

            snapshot_path = write_status_snapshot(args.root, args.change_id)
            snapshot = load_yaml(snapshot_path)
            print(format_status_snapshot_view(snapshot))
            _print_status_preflight(args.root, args.change_id)
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
                if maintenance.get("last_archived_change"):
                    from governance.status_views import last_archive_summary, render_last_archive_summary

                    print("")
                    print(render_last_archive_summary(last_archive_summary(args.root)), end="")
            print("- next_action: create or set an active change before running step matrix view")
            _print_status_preflight(args.root, None)
            return
        snapshot_path = write_status_snapshot(args.root)
        snapshot = load_yaml(snapshot_path)
        print(format_status_snapshot_view(snapshot))
        _print_status_preflight(args.root, snapshot.get("change_id"))
    except ContractValidationError as e:
        current = read_current_change(args.root)
        print(_format_draft_status_view(args.root, current, str(e)))
        _print_status_preflight(args.root, None)
    except Exception as e:
        print(f"Status check failed: {e}")
        print("Tip: Have you run 'ocw init' or set a current change?")


def _should_render_lean_status(args) -> bool:
    if getattr(args, "change_id", None):
        return False
    root = Path(args.root)
    return (root / ".governance/state.yaml").exists() and not (root / ".governance/index/current-change.yaml").exists()


def _print_lean_status(root: str | Path) -> None:
    from governance.lean_round import evaluate_closeout_gate, evaluate_execution_gate
    from governance.lean_state import load_lean_state, validate_lean_state

    state = load_lean_state(root)
    active_round = state.get("active_round", {})
    print("# open-cowork lean status")
    print("")
    print(f"- protocol: {state.get('protocol', {}).get('version')}")
    print(f"- layout: {state.get('layout')}")
    print(f"- round_id: {active_round.get('round_id')}")
    print(f"- goal: {active_round.get('goal')}")
    print(f"- phase: {active_round.get('phase')}")
    print(f"- participant_initialization: {active_round.get('participant_initialization', {}).get('status')}")
    errors = validate_lean_state(state)
    print(f"- schema_valid: {str(not errors).lower()}")
    if errors:
        print("- schema_errors:")
        for error in errors:
            print(f"  - {error}")
    execution = evaluate_execution_gate(state)
    closeout = evaluate_closeout_gate(state)
    print("## Gates")
    print(f"- execution: {execution.get('reason')} allowed={str(execution.get('allowed')).lower()}")
    print(f"- closeout: {closeout.get('reason')} allowed={str(closeout.get('allowed')).lower()}")
    print("")


def _print_status_preflight(root: str | Path, change_id: str | None) -> None:
    from governance.preflight import check_execution_preflight

    payload = check_execution_preflight(root, change_id)
    print("## Execution preflight")
    print(f"- can_modify_project_files: {str(payload.get('can_execute')).lower()}")
    print(f"- reason: {payload.get('reason')}")
    print(f"- required_action: {payload.get('required_action')}")
    if payload.get("contract_ref"):
        print(f"- contract_ref: {payload.get('contract_ref')}")
    if payload.get("evidence_ref"):
        print(f"- evidence_ref: {payload.get('evidence_ref')}")
    print("")


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
    from governance.step_matrix import STEP_LABELS

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
        f"- next_decision: Step 5 / {STEP_LABELS[5]}",
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
            session_log_path=getattr(args, "session_log", None),
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
        runtime = diagnosis.get("runtime_failure", {})
        print(f"- runtime_failure: {runtime.get('status')}")
        if runtime.get("last_error_at"):
            print(f"- runtime_failure_at: {runtime.get('last_error_at')}")
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
            session_log_path=getattr(args, "session_log", None),
        )
        print(f"Session recovery packet written: {output_path}")
    except Exception as e:
        print(f"Packet generation failed: {e}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="open-cowork CLI")
    parser.add_argument("--root", default=".", help="Project root directory")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_init = subparsers.add_parser("init", help="Initialize minimum governance directory")
    p_init.add_argument("--legacy-layout", action="store_true", help="Intentionally initialize the legacy heavy governance layout")
    subparsers.add_parser("propose", help="Create an intent draft")
    subparsers.add_parser("version", help="Show open-cowork version and command paths")
    p_activate = subparsers.add_parser("activate", help="Show project-scoped activation and handoff state")
    p_activate.add_argument("--change-id", default=None, help="Explicit active change to continue")
    p_activate.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_resume = subparsers.add_parser("resume", help="Deterministically resume open-cowork project work")
    p_resume.add_argument("--list", action="store_true", help="List active changes without selecting one")
    p_resume.add_argument("--change-id", default=None, help="Explicit active change to continue")
    p_resume.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_profile = subparsers.add_parser("profile", help="Manage collaboration modes")
    p_profile_sub = p_profile.add_subparsers(dest="profile_subcmd")
    p_profile_list = p_profile_sub.add_parser("list", help="List collaboration modes")
    p_profile_list.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_profile_show = p_profile_sub.add_parser("show", help="Show a collaboration mode")
    p_profile_show.add_argument("profile_id", help="Profile id")
    p_profile_show.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_profile_apply = p_profile_sub.add_parser("apply", help="Apply a collaboration mode")
    p_profile_apply.add_argument("profile_id", help="Profile id")
    p_profile_apply.add_argument("--agent-id", default="current-agent", help="Current Agent participant id")
    p_profile_apply.add_argument("--preview", action="store_true", help="Preview changes without writing")
    p_profile_apply.add_argument("--force", action="store_true", help="Overwrite existing adoption profile")
    p_profile_apply.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    p_context_pack = subparsers.add_parser("context-pack", help="Create or read handoff material indexes")
    p_context_pack_sub = p_context_pack.add_subparsers(dest="context_pack_subcmd")
    p_context_pack_create = p_context_pack_sub.add_parser("create", help="Create a handoff material index for a change")
    p_context_pack_create.add_argument("--change-id", required=True, help="Target change id")
    p_context_pack_create.add_argument("--level", choices=["minimal", "standard", "deep"], default="standard", help="Context pack level")
    p_context_pack_read = p_context_pack_sub.add_parser("read", help="Read a handoff material index for a change")
    p_context_pack_read.add_argument("--change-id", required=True, help="Target change id")
    p_context_pack_read.add_argument("--level", choices=["minimal", "standard", "deep"], default="standard", help="Context pack level")
    p_context_pack_read.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_handoff = subparsers.add_parser("handoff", help="Write a short handoff summary for a change")
    p_handoff.add_argument("--compact", action="store_true", help="Write a short handoff summary")
    p_handoff.add_argument("--change-id", required=True, help="Target change id")

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
        p_hygiene.add_argument("--cleanup", action="store_true", help="Preview or confirm v0.3.11 legacy cleanup")
        p_hygiene.add_argument("--dry-run", action="store_true", help="Preview cleanup without writing changes")
        p_hygiene.add_argument("--confirm", action="store_true", help="Confirm cleanup and write a receipt")

    p_migrate = subparsers.add_parser("migrate", help="Detect and migrate legacy governance layouts")
    p_migrate_sub = p_migrate.add_subparsers(dest="subcmd")
    p_migrate_sub.add_parser("detect", help="Detect legacy heavy governance directories")
    p_migrate_lean = p_migrate_sub.add_parser("lean", help="Migrate legacy governance to v0.3.11 lean layout")
    p_migrate_lean.add_argument("--dry-run", action="store_true", help="Preview migration without moving files")
    p_migrate_lean.add_argument("--confirm", action="store_true", help="Confirm migration and write a receipt")
    p_migrate_sub.add_parser("verify", help="Verify v0.3.11 lean migration outputs")

    p_uninstall = subparsers.add_parser("uninstall", help="Preview or confirm safe open-cowork governance uninstall")
    p_uninstall.add_argument("--dry-run", action="store_true", help="Preview uninstall without deleting files")
    p_uninstall.add_argument("--confirm", action="store_true", help="Confirm uninstall and write a receipt")

    p_participants = subparsers.add_parser("participants", help="Configure human and Agent participants")
    p_participants_sub = p_participants.add_subparsers(dest="subcmd")
    p_participants_setup = p_participants_sub.add_parser("setup", help="Write a participants profile and 9-step owner matrix")
    p_participants_setup.add_argument("--profile", choices=["personal", "team"], default="personal", help="Participants profile")
    p_participants_setup.add_argument("--participant", action="append", default=[], help="Participant spec, e.g. codex:executor,verifier")
    p_participants_setup.add_argument("--step-owner", action="append", default=[], help="Map a step owner, e.g. 6=coding-agent")
    p_participants_setup.add_argument("--step-assistant", action="append", default=[], help="Map a step assistant, e.g. 6=helper-agent")
    p_participants_setup.add_argument("--step-reviewer", action="append", default=[], help="Map a step reviewer, e.g. 8=review-agent")
    p_participants_setup.add_argument("--change-id", default=None, help="Optional change id whose bindings.yaml should be updated")
    p_participants_setup.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_participants_list = p_participants_sub.add_parser("list", help="List participants and step owner matrix")
    p_participants_list.add_argument("--change-id", default=None, help="Optional change id whose bindings.yaml should be included")
    p_participants_list.add_argument("--format", choices=["human", "text", "yaml", "json"], default="human", help="Output format")

    p_team = subparsers.add_parser("team", help="Team operating loop status and digest")
    p_team_sub = p_team.add_subparsers(dest="subcmd")
    p_team_status = p_team_sub.add_parser("status", help="Show team operating status")
    p_team_status.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_team_digest = p_team_sub.add_parser("digest", help="Show team digest")
    p_team_digest.add_argument("--period", choices=["daily", "weekly"], default="daily", help="Digest period")
    p_team_digest.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_participant = subparsers.add_parser("participant", help="Discover, register, list, update, and assign collaboration participants")
    p_participant_sub = p_participant.add_subparsers(dest="subcmd")
    p_participant_discover = p_participant_sub.add_parser("discover", help="Discover local personal-domain Agent candidates")
    p_participant_discover.add_argument("--recorded-by", default="agent", help="Actor recording discovery")
    p_participant_discover.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_participant_register = p_participant_sub.add_parser("register", help="Register a local or remote participant")
    p_participant_register.add_argument("--participant-id", required=True, help="Participant id")
    p_participant_register.add_argument("--type", choices=["human", "agent"], default="agent", help="Participant type")
    p_participant_register.add_argument("--domain", choices=["personal-local", "team-remote", "team-local"], default="personal-local", help="Participant domain")
    p_participant_register.add_argument("--entrypoint", default="", help="CLI, URL, declared contact, or remote invitation ref")
    p_participant_register.add_argument("--capability", action="append", default=[], help="Capability")
    p_participant_register.add_argument("--default-role", action="append", default=[], help="Default role")
    p_participant_register.add_argument("--step", type=int, action="append", default=[], help="Eligible step")
    p_participant_register.add_argument("--remote", action="store_true", help="Participant is remote and declarative, not locally callable")
    p_participant_register.add_argument("--recorded-by", required=True, help="Actor recording registration")
    p_participant_register.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_participant_list = p_participant_sub.add_parser("list", help="List team participants")
    p_participant_list.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_participant_assign = p_participant_sub.add_parser("assign", help="Assign a participant to a change step")
    p_participant_assign.add_argument("--participant-id", required=True, help="Participant id")
    p_participant_assign.add_argument("--change-id", required=True, help="Target change id")
    p_participant_assign.add_argument("--step", type=int, required=True, help="Step number")
    p_participant_assign.add_argument("--role", choices=["owner", "executor", "reviewer", "participant"], required=True, help="Role")
    p_participant_assign.add_argument("--recorded-by", required=True, help="Actor recording assignment")
    p_participant_assign.add_argument("--note", default="", help="Assignment note")
    p_participant_assign.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_participant_update = p_participant_sub.add_parser("update", help="Update a participant")
    p_participant_update.add_argument("--participant-id", required=True, help="Participant id")
    p_participant_update.add_argument("--domain", default=None, help="Updated domain")
    p_participant_update.add_argument("--entrypoint", default=None, help="Updated entrypoint")
    p_participant_update.add_argument("--capability", action="append", default=[], help="Replacement capability")
    p_participant_update.add_argument("--default-role", action="append", default=[], help="Replacement default role")
    p_participant_update.add_argument("--step", type=int, action="append", default=[], help="Replacement eligible step")
    p_participant_update.add_argument("--remote", action="store_true", help="Mark as remote")
    p_participant_update.add_argument("--recorded-by", required=True, help="Actor recording update")
    p_participant_update.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_assignment = subparsers.add_parser("assignment", help="Set team assignments")
    p_assignment.add_argument("subcmd", choices=["set"], help="Assignment action")
    p_assignment.add_argument("--change-id", required=True, help="Target change id")
    p_assignment.add_argument("--step", type=int, required=True, help="Step number")
    p_assignment.add_argument("--role", choices=["owner", "executor", "reviewer", "participant"], required=True, help="Role")
    p_assignment.add_argument("--actor", required=True, help="Assigned actor")
    p_assignment.add_argument("--recorded-by", required=True, help="Actor recording assignment")
    p_assignment.add_argument("--note", default="", help="Assignment note")
    p_assignment.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_blocked = subparsers.add_parser("blocked", help="Set or clear team blockers")
    p_blocked_sub = p_blocked.add_subparsers(dest="subcmd")
    p_blocked_set = p_blocked_sub.add_parser("set", help="Set a blocker")
    p_blocked_set.add_argument("--change-id", required=True, help="Target change id")
    p_blocked_set.add_argument("--reason", required=True, help="Block reason")
    p_blocked_set.add_argument("--waiting-on", required=True, help="Who or what is blocking")
    p_blocked_set.add_argument("--next-decision", required=True, help="Next decision")
    p_blocked_set.add_argument("--recorded-by", required=True, help="Actor recording blocker")
    p_blocked_set.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_blocked_clear = p_blocked_sub.add_parser("clear", help="Clear a blocker")
    p_blocked_clear.add_argument("--block-id", required=True, help="Block id")
    p_blocked_clear.add_argument("--recorded-by", required=True, help="Actor clearing blocker")
    p_blocked_clear.add_argument("--resolution", default="", help="Resolution note")
    p_blocked_clear.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_reviewer = subparsers.add_parser("reviewer", help="Manage reviewer queue")
    p_reviewer_sub = p_reviewer.add_subparsers(dest="subcmd")
    p_reviewer_queue = p_reviewer_sub.add_parser("queue", help="List or enqueue reviewer work")
    p_reviewer_queue.add_argument("--change-id", default=None, help="Target change id to enqueue; omit to list")
    p_reviewer_queue.add_argument("--reviewer", default="", help="Reviewer id")
    p_reviewer_queue.add_argument("--priority", choices=["low", "normal", "high", "urgent"], default="normal", help="Priority")
    p_reviewer_queue.add_argument("--recorded-by", default="", help="Actor recording queue entry")
    p_reviewer_queue.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_recurring = subparsers.add_parser("recurring-intent", help="Manage recurring intents")
    p_recurring_sub = p_recurring.add_subparsers(dest="subcmd")
    p_recurring_add = p_recurring_sub.add_parser("add", help="Add recurring intent")
    p_recurring_add.add_argument("--intent-id", required=True, help="Intent id")
    p_recurring_add.add_argument("--summary", required=True, help="Intent summary")
    p_recurring_add.add_argument("--cadence", required=True, help="Cadence")
    p_recurring_add.add_argument("--recorded-by", required=True, help="Actor recording intent")
    p_recurring_add.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_recurring_trigger = p_recurring_sub.add_parser("trigger", help="Trigger recurring intent into a governed change draft")
    p_recurring_trigger.add_argument("--intent-id", required=True, help="Intent id")
    p_recurring_trigger.add_argument("--change-id", required=True, help="New change id")
    p_recurring_trigger.add_argument("--recorded-by", required=True, help="Actor recording trigger")
    p_recurring_trigger.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_carry = subparsers.add_parser("carry-forward", help="Manage carry-forward candidates")
    p_carry_sub = p_carry.add_subparsers(dest="subcmd")
    p_carry_list = p_carry_sub.add_parser("list", help="List carry-forward candidates")
    p_carry_list.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_carry_add = p_carry_sub.add_parser("add", help="Add carry-forward candidate")
    p_carry_add.add_argument("--item-id", required=True, help="Item id")
    p_carry_add.add_argument("--summary", required=True, help="Summary")
    p_carry_add.add_argument("--source-change-id", required=True, help="Source change id")
    p_carry_add.add_argument("--recorded-by", required=True, help="Actor recording item")
    p_carry_add.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_carry_promote = p_carry_sub.add_parser("promote", help="Promote carry-forward candidate into a governed change draft")
    p_carry_promote.add_argument("--item-id", required=True, help="Item id")
    p_carry_promote.add_argument("--change-id", required=True, help="New change id")
    p_carry_promote.add_argument("--recorded-by", required=True, help="Actor recording promotion")
    p_carry_promote.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_retro = subparsers.add_parser("retrospective", help="Manage team retrospectives")
    p_retro_sub = p_retro.add_subparsers(dest="subcmd")
    p_retro_add = p_retro_sub.add_parser("add", help="Add team retrospective")
    p_retro_add.add_argument("--retrospective-id", required=True, help="Retrospective id")
    p_retro_add.add_argument("--change-id", required=True, help="Change id")
    p_retro_add.add_argument("--summary", required=True, help="Summary")
    p_retro_add.add_argument("--learning", action="append", default=[], help="Learning")
    p_retro_add.add_argument("--recorded-by", required=True, help="Actor recording retrospective")
    p_retro_add.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_retro_list = p_retro_sub.add_parser("list", help="List team retrospectives")
    p_retro_list.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

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
    p_intent_status = p_intent_sub.add_parser("status", help="Show captured intent status")
    p_intent_status.add_argument("--change-id", required=True, help="Target change id")
    p_intent_status.add_argument("--format", choices=["human", "text", "yaml", "json"], default="human", help="Output format")

    p_step = subparsers.add_parser("step", help="Create human-visible step reports")
    p_step_sub = p_step.add_subparsers(dest="subcmd")
    p_step_report = p_step_sub.add_parser("report", help="Write a report for a 9-step workflow step")
    p_step_report.add_argument("--change-id", required=True, help="Target change id")
    p_step_report.add_argument("--step", type=int, default=None, help="Step number, defaults to current step")
    p_step_report.add_argument("--format", choices=["text", "yaml", "json", "human"], default="text", help="Output format")
    p_step_approve = p_step_sub.add_parser("approve", help="Record human approval for a gated step")
    p_step_approve.add_argument("--change-id", required=True, help="Target change id")
    p_step_approve.add_argument("--step", type=int, required=True, help="Step number to approve")
    p_step_approve.add_argument("--approved-by", required=True, help="Human or sponsor approving the step")
    p_step_approve.add_argument("--recorded-by", default="", help="Agent or participant recording the approval")
    p_step_approve.add_argument("--evidence-ref", default="", help="Evidence reference for the approval")
    p_step_approve.add_argument("--approval-token", default="", help="Sponsor-held approval token when this change requires trusted approval")
    p_step_approve.add_argument("--note", default="", help="Approval note")
    p_step_approve.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    p_change = subparsers.add_parser("change", help="Change package management")
    p_change.add_argument("subcmd", choices=["create", "prepare", "status"], help="Create, prepare, or inspect change package")
    p_change.add_argument("change_id", nargs="?", help="Change identifier")
    p_change.add_argument("--change-id", dest="change_id_flag", default=None, help="Target change id for status")
    p_change.add_argument("--title", default="", help="Optional change title")
    p_change.add_argument("--goal", default="", help="Change goal for generated authoring files")
    p_change.add_argument("--scope-in", action="append", default=[], help="Allowed implementation path or glob")
    p_change.add_argument("--scope-out", action="append", default=[], help="Excluded path or glob")
    p_change.add_argument("--verify-command", action="append", default=[], help="Verification command")
    p_change.add_argument("--source-doc", action="append", default=[], help="Source document path")
    p_change.add_argument("--active-policy", choices=["continue", "supersede", "abandon", "archive-first", "force"], default=None, help="Policy for unresolved active change conflicts")
    p_change.add_argument("--profile", choices=["personal", "team"], default="personal", help="Role binding profile")
    p_change.add_argument("--format", choices=["human", "text", "yaml", "json"], default="human", help="Output format for status")

    p_index = subparsers.add_parser("index", help="Governance index maintenance")
    p_index_sub = p_index.add_subparsers(dest="subcmd")
    p_index_rebuild = p_index_sub.add_parser("rebuild", help="Rebuild merge-safe governance indexes from authoritative facts")
    p_index_rebuild.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_contract = subparsers.add_parser("contract", help="Contract management")
    p_contract_sub = p_contract.add_subparsers(dest="subcmd")
    p_contract_validate = p_contract_sub.add_parser("validate", help="Validate contract for a change")
    p_contract_validate.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_contract_validate.add_argument("--path", default=None, help="Optional explicit contract path")

    p_preflight = subparsers.add_parser("preflight", help="Check execution readiness before modifying project files")
    p_preflight_sub = p_preflight.add_subparsers(dest="subcmd")
    p_preflight_check = p_preflight_sub.add_parser("check", help="Check whether project files may be modified")
    p_preflight_check.add_argument("--change-id", default=None, help="Target change id (defaults to current active change)")
    p_preflight_check.add_argument("--path", action="append", default=[], help="Project file path intended for modification; repeat to check multiple paths against contract scope")
    p_preflight_check.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")
    p_preflight_recovery = p_preflight_sub.add_parser("recovery", help="Record an exceptional recovery for bypassed governance flow")
    p_preflight_recovery.add_argument("--change-id", required=True, help="Target change id")
    p_preflight_recovery.add_argument("--reason", required=True, help="Why normal preflight was bypassed")
    p_preflight_recovery.add_argument("--modified", action="append", default=[], help="File modified before governance preflight")
    p_preflight_recovery.add_argument("--missing", action="append", default=[], help="Missing governance item, e.g. contract/evidence/review")
    p_preflight_recovery.add_argument("--action", action="append", default=[], help="Recovery action taken or required")
    p_preflight_recovery.add_argument("--recorded-by", required=True, help="Actor recording the recovery")
    p_preflight_recovery.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_audit = subparsers.add_parser("audit", help="Audit governance invariants before verify, review, or archive")
    p_audit.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_audit.add_argument("--format", choices=["text", "yaml", "json"], default="text", help="Output format")

    p_run = subparsers.add_parser("run", help="Execute change adapter")
    p_run.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_run.add_argument("--timeout-seconds", type=int, default=60, help="Execution timeout in seconds")
    p_run.add_argument("--command", dest="exec_command", default=None, help="Command description for evidence")
    p_run.add_argument("--command-output", default="", help="Command output summary")
    p_run.add_argument("--test-output", default="", help="Test output summary")
    p_run.add_argument("--created", action="append", default=[], help="Created artifact path")
    p_run.add_argument("--modified", action="append", default=[], help="Modified artifact path")
    p_run.add_argument("--evidence-ref", action="append", default=[], help="Additional evidence reference path")

    p_runtime = subparsers.add_parser("runtime", help="Manage runtime profiles")
    p_runtime_sub = p_runtime.add_subparsers(dest="runtime_subcmd")
    p_runtime_profile = p_runtime_sub.add_parser("profile", help="Manage runtime profiles")
    p_runtime_profile_sub = p_runtime_profile.add_subparsers(dest="profile_action")
    p_runtime_profile_add = p_runtime_profile_sub.add_parser("add", help="Add runtime profile")
    p_runtime_profile_add.add_argument("--runtime-id", required=True)
    p_runtime_profile_add.add_argument("--runtime-type", default="local-cli")
    p_runtime_profile_add.add_argument("--owner", default="unassigned")
    p_runtime_profile_add.add_argument("--capability", action="append", default=[])
    p_runtime_profile_add.add_argument("--risk", action="append", default=[])
    p_runtime_profile_add.add_argument("--evidence", action="append", default=[])
    p_runtime_profile_add.add_argument("--constraint", action="append", default=[])
    p_runtime_profile_add.add_argument("--format", choices=["text", "yaml", "json"], default="text")
    p_runtime_profile_list = p_runtime_profile_sub.add_parser("list", help="List runtime profiles")
    p_runtime_profile_list.add_argument("--format", choices=["text", "yaml", "json"], default="text")
    p_runtime_profile_show = p_runtime_profile_sub.add_parser("show", help="Show runtime profile")
    p_runtime_profile_show.add_argument("runtime_id")
    p_runtime_profile_show.add_argument("--format", choices=["text", "yaml", "json"], default="text")

    p_runtime_event = subparsers.add_parser("runtime-event", help="Append change runtime event")
    p_runtime_event.add_argument("subcmd", choices=["append"])
    p_runtime_event.add_argument("--change-id", required=True)
    p_runtime_event.add_argument("--event-type", required=True)
    p_runtime_event.add_argument("--step", type=int, required=True)
    p_runtime_event.add_argument("--actor-id", default="governance")
    p_runtime_event.add_argument("--ref", action="append", default=[])
    p_runtime_event.add_argument("--authority", choices=["trace_only", "evidence_input", "verification_result"], default="trace_only")
    p_runtime_event.add_argument("--format", choices=["text", "yaml", "json"], default="text")

    p_adapter = subparsers.add_parser("adapter", help="Validate adapter outputs")
    p_adapter.add_argument("subcmd", choices=["validate-output"])
    p_adapter.add_argument("path")
    p_adapter.add_argument("--format", choices=["text", "yaml", "json"], default="text")

    p_round = subparsers.add_parser("round", help="Manage lean protocol rounds")
    p_round_sub = p_round.add_subparsers(dest="round_subcmd")
    p_round_start = p_round_sub.add_parser("start", help="Start a lean round")
    p_round_start.add_argument("--round-id", required=True)
    p_round_start.add_argument("--goal", required=True)
    p_round_start.add_argument("--scope-in", action="append", default=[])
    p_round_start.add_argument("--scope-out", action="append", default=[])
    p_round_start.add_argument("--acceptance", default="")
    p_round_participants = p_round_sub.add_parser("participants", help="Initialize round participants")
    p_round_participants_sub = p_round_participants.add_subparsers(dest="participants_subcmd")
    p_round_participants_init = p_round_participants_sub.add_parser("init", help="Initialize required roles")
    p_round_participants_init.add_argument("--sponsor", required=True)
    p_round_participants_init.add_argument("--owner-agent", required=True)
    p_round_participants_init.add_argument("--orchestrator", default="")
    p_round_participants_init.add_argument("--executor", required=True)
    p_round_participants_init.add_argument("--reviewer", required=True)
    p_round_participants_init.add_argument("--advisor", action="append", default=[])
    p_round_approve = p_round_sub.add_parser("approve", help="Approve a lean gate")
    p_round_approve.add_argument("--gate", choices=["execution", "closeout"], required=True)
    p_round_approve.add_argument("--approved-by", required=True)
    p_round_approve.add_argument("--evidence-ref", required=True)
    p_round_approve.add_argument("--reason", default="")
    p_round_close = p_round_sub.add_parser("close", help="Close a lean round into the ledger")
    p_round_close.add_argument("--final-status", choices=["completed", "cancelled", "blocked"], default="completed")
    p_round_close.add_argument("--closed-by", required=True)
    p_round_close.add_argument("--summary", default="")
    p_round_close.add_argument("--evidence-ref", default="")

    p_rule = subparsers.add_parser("rule", help="Manage lean external rules")
    p_rule_sub = p_rule.add_subparsers(dest="rule_subcmd")
    p_rule_add = p_rule_sub.add_parser("add", help="Add an external rule")
    p_rule_add.add_argument("--id", required=True)
    p_rule_add.add_argument("--name", required=True)
    p_rule_add.add_argument("--kind", required=True)
    p_rule_add.add_argument("--failure-impact", choices=["blocking", "warning", "advisory"], required=True)
    p_rule_add.add_argument("--applies-to", action="append", default=[])
    p_rule_add.add_argument("--command", dest="rule_command", default="")
    p_rule_add.add_argument("--authorization-ref", default="")
    for action in ("suspend", "resume", "remove"):
        p_rule_action = p_rule_sub.add_parser(action, help=f"{action.title()} an external rule")
        p_rule_action.add_argument("--id", required=True)
        p_rule_action.add_argument("--reason", default="")
        p_rule_action.add_argument("--actor", default="agent")
        p_rule_action.add_argument("--authorization-ref", default="")

    p_evidence = subparsers.add_parser("evidence", help="Manage evidence indexes")
    p_evidence_sub = p_evidence.add_subparsers(dest="evidence_subcmd")
    p_evidence_add = p_evidence_sub.add_parser("add", help="Add lean evidence")
    p_evidence_add.add_argument("--id", required=True)
    p_evidence_add.add_argument("--kind", required=True)
    p_evidence_add.add_argument("--ref", required=True)
    p_evidence_add.add_argument("--summary", required=True)
    p_evidence_add.add_argument("--created-by", required=True)
    p_evidence_add.add_argument("--round-id", default=None)
    p_evidence_index = p_evidence_sub.add_parser("index", help="Generate evidence index")
    p_evidence_index.add_argument("--change-id", required=True)
    p_evidence_append = p_evidence_sub.add_parser("append", help="Append adapter output evidence")
    p_evidence_append.add_argument("--change-id", required=True)
    p_evidence_append.add_argument("--adapter", required=True, help="Adapter output YAML path")

    p_verify = subparsers.add_parser("verify", help="Verify execution results")
    p_verify.add_argument("--change-id", required=True, help="Target change id")
    p_verify.add_argument("--run-commands", action="store_true", help="Run contract verification commands in addition to governance state checks")
    p_verify.add_argument("--timeout-seconds", type=int, default=120, help="Timeout for each verification command")

    p_review = subparsers.add_parser("review", help="Record independent review decision")
    p_review.add_argument("--change-id", required=True, help="Target change id")
    p_review.add_argument("--decision", choices=["approve", "reject", "revise"], required=True, help="Review decision")
    p_review.add_argument("--reviewer", required=True, help="Reviewer identifier")
    p_review.add_argument("--rationale", default="", help="Decision rationale")
    p_review.add_argument("--allow-reviewer-mismatch", action="store_true", help="Allow a reviewer mismatch and record an audit bypass")
    p_review.add_argument("--bypass-reason", default="", help="Human-readable reviewer mismatch bypass reason")
    p_review.add_argument("--bypass-recorded-by", default="", help="Actor recording reviewer mismatch risk acceptance")
    p_review.add_argument("--bypass-evidence-ref", default="", help="Evidence reference for reviewer mismatch risk acceptance")
    p_review.add_argument("--runtime", default="", help="Actual reviewer runtime or local agent used")
    p_review.add_argument("--health-check", default="", help="Reviewer runtime health check status")
    p_review.add_argument("--invocation-status", default="", help="Reviewer runtime invocation status")
    p_review.add_argument("--failure-reason", default="", help="Reviewer runtime failure reason")
    p_review.add_argument("--fallback-reviewer", default="", help="Fallback reviewer actor when primary failed")
    p_review.add_argument("--review-artifact-ref", default="", help="Review artifact produced by actual reviewer")

    p_review_invocation = subparsers.add_parser("review-invocation", help="Record reviewer invocation progress or heartbeat")
    p_review_invocation.add_argument("--change-id", required=True, help="Target change id")
    p_review_invocation.add_argument("--status", choices=["started", "running", "completed", "failed", "timeout"], required=True, help="Reviewer invocation status")
    p_review_invocation.add_argument("--reviewer", required=True, help="Reviewer identifier")
    p_review_invocation.add_argument("--runtime", default="", help="Actual reviewer runtime or local agent used")
    p_review_invocation.add_argument("--note", default="", help="Progress note or heartbeat detail")
    p_review_invocation.add_argument("--timeout-policy", default="", help="Timeout policy for this reviewer invocation")
    p_review_invocation.add_argument("--artifact-ref", default="", help="Progress or final artifact reference")

    p_archive = subparsers.add_parser("archive", help="Archive and refresh state")
    p_archive.add_argument("--change-id", required=True, help="Target change id")
    p_status = subparsers.add_parser("status", help="Show current step, gate status, and blockers")
    p_status.add_argument("--sync-current-state", action="store_true", help="Refresh .governance/current-state.md from current index/runtime state")
    p_status.add_argument("--change-id", default=None, help="Show status for a specific change")
    p_status.add_argument("--last-archive", action="store_true", help="Show the last archived closeout summary")
    p_revise = subparsers.add_parser("revise", help="Open a revision loop after review revise")
    p_revise.add_argument("--change-id", required=True, help="Target change id")
    p_revise.add_argument("--reason", required=True, help="Revision reason")
    p_revise.add_argument("--recorded-by", required=True, help="Actor recording the revision")
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
    p_diag.add_argument("--session-log", default=None, help="Optional Codex session jsonl path for runtime failure diagnosis")
    p_packet = subparsers.add_parser("session-recovery-packet", help="Write session recovery diagnosis packet YAML")
    p_packet.add_argument("--change-id", default=None, help="Optional target change id override")
    p_packet.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet.add_argument("--output", default=None, help="Optional output yaml path")
    p_packet.add_argument("--session-log", default=None, help="Optional Codex session jsonl path for runtime failure diagnosis")
    p_diag_alias = subparsers.add_parser("diagnose-hermes", help="Alias of diagnose-session")
    p_diag_alias.add_argument("--change-id", default=None, help="Optional target change id override")
    p_diag_alias.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_diag_alias.add_argument("--session-log", default=None, help="Optional Codex session jsonl path for runtime failure diagnosis")
    p_packet_alias = subparsers.add_parser("hermes-recovery-packet", help="Alias of session-recovery-packet")
    p_packet_alias.add_argument("--change-id", default=None, help="Optional target change id override")
    p_packet_alias.add_argument("--context-budget", type=int, default=12000, help="Context budget in tokens")
    p_packet_alias.add_argument("--output", default=None, help="Optional output yaml path")
    p_packet_alias.add_argument("--session-log", default=None, help="Optional Codex session jsonl path for runtime failure diagnosis")
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
    elif args.command == "activate":
        return cmd_activate(args)
    elif args.command == "resume":
        return cmd_resume(args)
    elif args.command == "profile":
        return cmd_profile(args)
    elif args.command == "context-pack":
        return cmd_context_pack(args)
    elif args.command == "handoff":
        return cmd_handoff(args)
    elif args.command in {"hygiene", "doctor"}:
        return cmd_hygiene(args)
    elif args.command == "migrate":
        return cmd_migrate(args)
    elif args.command == "uninstall":
        return cmd_uninstall(args)
    elif args.command == "participants" and args.subcmd == "setup":
        return cmd_participants_setup(args)
    elif args.command == "participants" and args.subcmd == "list":
        return cmd_participants_list(args)
    elif args.command == "team":
        return cmd_team(args)
    elif args.command == "participant":
        return cmd_participant(args)
    elif args.command == "assignment":
        return cmd_assignment(args)
    elif args.command == "blocked":
        return cmd_blocked(args)
    elif args.command == "reviewer":
        return cmd_reviewer(args)
    elif args.command == "recurring-intent":
        return cmd_recurring_intent(args)
    elif args.command == "carry-forward":
        return cmd_carry_forward(args)
    elif args.command == "retrospective":
        return cmd_retrospective(args)
    elif args.command == "intent" and args.subcmd == "capture":
        return cmd_intent_capture(args)
    elif args.command == "intent" and args.subcmd == "confirm":
        return cmd_intent_confirm(args)
    elif args.command == "intent" and args.subcmd == "status":
        return cmd_intent_status(args)
    elif args.command == "step" and args.subcmd == "report":
        return cmd_step_report(args)
    elif args.command == "step" and args.subcmd == "approve":
        return cmd_step_approve(args)
    elif args.command == "change" and args.subcmd == "create":
        cmd_change_create(args)
    elif args.command == "change" and args.subcmd == "prepare":
        return cmd_change_prepare(args)
    elif args.command == "change" and args.subcmd == "status":
        return cmd_change_status(args)
    elif args.command == "index" and args.subcmd == "rebuild":
        return cmd_index_rebuild(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "contract" and args.subcmd == "validate":
        return cmd_contract_validate(args)
    elif args.command == "preflight":
        return cmd_preflight(args)
    elif args.command == "audit":
        return cmd_audit(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "runtime":
        return cmd_runtime(args)
    elif args.command == "runtime-event" and args.subcmd == "append":
        return cmd_runtime_event(args)
    elif args.command == "adapter" and args.subcmd == "validate-output":
        return cmd_adapter(args)
    elif args.command == "round":
        return cmd_round(args)
    elif args.command == "rule":
        return cmd_rule(args)
    elif args.command == "evidence":
        return cmd_evidence(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "review":
        return cmd_review(args)
    elif args.command == "review-invocation":
        return cmd_review_invocation(args)
    elif args.command == "archive":
        return cmd_archive(args)
    elif args.command == "revise":
        return cmd_revise(args)
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
