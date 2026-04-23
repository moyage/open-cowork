from __future__ import annotations

import argparse
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

    try:
        contract_path = Path(args.path) if args.path else read_change_package(args.root, args.change_id).path / "contract.yaml"
        load_contract(contract_path)
        print(f"Contract valid: {contract_path}")
        return 0
    except (ValueError, ContractValidationError) as exc:
        print(f"Contract invalid: {exc}")
        return 1


def cmd_run(args):
    from governance.change_package import read_change_package, update_manifest
    from governance.index import read_current_change, set_current_change, set_maintenance_status, upsert_change_entry
    from governance.run import AdapterRequest, run_change

    package = read_change_package(args.root, args.change_id)
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
    print(f"Run completed: {package.change_id} ({response.run_id})")
    return 0


def cmd_verify(args):
    from governance.verify import write_verify_result

    try:
        payload = write_verify_result(args.root, args.change_id)
        print(f"Verify recorded: {payload['change_id']} -> {payload['summary']['status']}")
        return 0
    except Exception as exc:
        print(f"Verify failed: {exc}")
        return 1


def cmd_review(args):
    from governance.review import write_review_decision

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
        print(f"Review failed: {exc}")
        return 1


def cmd_archive(args):
    from governance.archive import archive_change

    try:
        receipt = archive_change(args.root, args.change_id)
        print(f"Archived change {receipt['change_id']} at {receipt['archived_at']}")
        return 0
    except Exception as exc:
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
    p_continuity = subparsers.add_parser("continuity", help="Materialize minimum continuity outputs")
    p_continuity_sub = p_continuity.add_subparsers(dest="subcmd")
    p_continuity_launch = p_continuity_sub.add_parser("launch-input", help="Write continuity launch input yaml")
    p_continuity_launch.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
    p_continuity_round = p_continuity_sub.add_parser("round-entry-summary", help="Write round entry summary yaml")
    p_continuity_round.add_argument("--change-id", default=None, help="Target change id (defaults to current change)")
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
    elif args.command == "continuity" and args.subcmd == "launch-input":
        return cmd_continuity_launch_input(args)
    elif args.command == "continuity" and args.subcmd == "round-entry-summary":
        return cmd_continuity_round_entry_summary(args)
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
