from __future__ import annotations

import argparse
import json
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
    )
    response = run_change(args.root, request)
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


def cmd_status(args):
    from governance.index import read_current_change
    from governance.simple_yaml import load_yaml
    from governance.step_matrix import format_status_snapshot_view, write_status_snapshot

    try:
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
    except Exception as e:
        print(f"Status check failed: {e}")
        print("Tip: Have you run 'ocw init' or set a current change?")


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
        )
    else:
        payload = read_sync_history(
            args.root,
            month=args.month,
            change_id=args.change_id,
            source_kind=args.source_kind,
            sync_kind=args.sync_kind,
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
    from governance.continuity import resolve_continuity_digest

    payload = resolve_continuity_digest(args.root, args.change_id)
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
    for ref in payload["recommended_reading"].get("secondary_refs", []):
        print(f"- {ref}")
    return 0


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
    parser = argparse.ArgumentParser(description="open-cowork MVP CLI")
    parser.add_argument("--root", default=".", help="Project root directory")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Initialize minimum governance directory")
    subparsers.add_parser("propose", help="Create an intent draft")

    p_change = subparsers.add_parser("change", help="Change package management")
    p_change.add_argument("subcmd", choices=["create"], help="Create change package")
    p_change.add_argument("change_id", help="Change identifier")
    p_change.add_argument("--title", default="", help="Optional change title")

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

    p_verify = subparsers.add_parser("verify", help="Verify execution results")
    p_verify.add_argument("--change-id", required=True, help="Target change id")

    p_review = subparsers.add_parser("review", help="Review and decide on change")
    p_review.add_argument("--change-id", required=True, help="Target change id")
    p_review.add_argument("--decision", choices=["approve", "reject", "revise"], required=True, help="Review decision")
    p_review.add_argument("--reviewer", required=True, help="Reviewer identifier")
    p_review.add_argument("--rationale", default="", help="Decision rationale")

    p_archive = subparsers.add_parser("archive", help="Archive and refresh state")
    p_archive.add_argument("--change-id", required=True, help="Target change id")
    subparsers.add_parser("status", help="Show current step, gate status, and blockers")
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
    elif args.command == "change" and args.subcmd == "create":
        cmd_change_create(args)
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
