from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from .index import read_current_change
from .paths import GovernancePaths
from .simple_yaml import load_yaml


def run_governance_audit(root: str | Path, change_id: str | None = None) -> dict:
    paths = GovernancePaths(Path(root))
    resolved_change_id = change_id or _current_change_id(paths)
    payload = {
        "schema": "governance-audit/v1",
        "change_id": resolved_change_id,
        "status": "fail",
        "generated_at": _now_utc(),
        "checks": [],
        "summary": {"pass": 0, "warning": 0, "fail": 0},
    }
    if not paths.governance_dir.exists():
        _add_check(payload, "A000", "governance_directory", "fail", "governance directory is missing", ".governance/")
        return _finalize(payload)
    if not resolved_change_id:
        _add_check(payload, "A001", "change_selection", "fail", "no change_id provided and no active change is set", ".governance/index/current-change.yaml")
        return _finalize(payload)

    change_dir = paths.change_dir(str(resolved_change_id))
    if not change_dir.exists():
        _add_check(payload, "A002", "change_package", "fail", f"change package '{resolved_change_id}' is missing", f".governance/changes/{resolved_change_id}/")
        return _finalize(payload)

    manifest = _load_optional(change_dir / "manifest.yaml")
    archive_dir = paths.archived_change_dir(str(resolved_change_id))
    archived = manifest.get("status") == "archived" and archive_dir.exists()
    fact_dir = archive_dir if archived else change_dir
    manifest = _load_optional(fact_dir / "manifest.yaml") or manifest
    contract = _load_optional(fact_dir / "contract.yaml")
    bindings = _load_optional(fact_dir / "bindings.yaml")
    gates = _load_optional(fact_dir / "human-gates.yaml")
    review = _load_optional(fact_dir / "review.yaml")
    base_ref = ".governance/archive" if archived else ".governance/changes"

    _audit_required_files(payload, fact_dir, str(resolved_change_id), base_ref=base_ref)
    if archived:
        _audit_archived_state_consistency(payload, paths.root, str(resolved_change_id), archive_dir)
    else:
        _audit_state_consistency(payload, paths.root, str(resolved_change_id))
    _audit_step_outputs(payload, fact_dir, manifest, base_ref=base_ref)
    _audit_step_output_contract(payload, fact_dir, manifest, contract, str(resolved_change_id), base_ref=base_ref)
    _audit_baseline(payload, fact_dir, manifest, contract, gates)
    _audit_human_gate_reconciliation(payload, fact_dir, bindings, gates)
    _audit_writer_metadata(payload, fact_dir, manifest, contract)
    _audit_canonical_artifacts(payload, fact_dir, manifest, contract)
    _audit_rule_sources(payload, paths.root, fact_dir, str(resolved_change_id))
    _audit_scope(payload, fact_dir, contract)
    _audit_recovery(payload, fact_dir, str(resolved_change_id))
    _audit_reviewer_separation(payload, bindings, review)
    _audit_review_closure(payload, review, gates)
    return _finalize(payload)


def format_governance_audit(payload: dict) -> str:
    lines = [
        "# open-cowork governance audit",
        "",
        f"- status: {payload.get('status')}",
        f"- change_id: {payload.get('change_id') or 'none'}",
    ]
    summary = payload.get("summary") or {}
    lines.append(f"- summary: pass={summary.get('pass', 0)} warning={summary.get('warning', 0)} fail={summary.get('fail', 0)}")
    lines.append("")
    lines.append("## Checks")
    for check in payload.get("checks") or []:
        lines.append(f"- {check.get('id')} {check.get('status')}: {check.get('name')} - {check.get('message')}")
        if check.get("ref"):
            lines.append(f"  ref: {check.get('ref')}")
        if check.get("required_action"):
            lines.append(f"  required_action: {check.get('required_action')}")
    return "\n".join(lines) + "\n"


def audit_failures_for_gate(payload: dict, gate: str) -> list[dict]:
    failures = [item for item in payload.get("checks", []) if item.get("status") == "fail"]
    if gate in {"preflight", "verify", "review"}:
        allowed = {
            "required_manifest.yaml",
            "required_contract.yaml",
            "required_bindings.yaml",
            "required_human-gates.yaml",
            "baseline_canonical_artifact",
            "step5_baseline_approval_binding",
            "baseline_reference_digests",
            "human_gate_reconciliation",
            "canonical_artifact_consistency",
            "rule_sources",
            "changed_files_scope",
            "flow_bypass_recovery",
        }
        if gate == "review":
            allowed.update({"reviewer_independence", "writer_metadata"})
        return [item for item in failures if item.get("name") in allowed]
    return failures


def _audit_required_files(payload: dict, change_dir: Path, change_id: str, *, base_ref: str = ".governance/changes") -> None:
    for name in ("manifest.yaml", "contract.yaml", "bindings.yaml", "human-gates.yaml"):
        status = "pass" if (change_dir / name).exists() else "fail"
        _add_check(
            payload,
            f"A1-{name}",
            f"required_{name}",
            status,
            f"{name} {'exists' if status == 'pass' else 'is missing'}",
            f"{base_ref}/{change_id}/{name}",
            "complete the change package before proceeding" if status == "fail" else "",
        )


def _audit_state_consistency(payload: dict, root: Path, change_id: str) -> None:
    try:
        from .state_consistency import evaluate_state_consistency

        result = evaluate_state_consistency(root, change_id)
        blockers = [item for item in result.get("checks", []) if item.get("status") == "blocker"]
        status = "fail" if blockers else "pass"
        message = "state consistency blockers found" if blockers else "state consistency passed"
        _add_check(payload, "A200", "state_consistency", status, message, f".governance/changes/{change_id}/manifest.yaml")
    except Exception as exc:
        _add_check(
            payload,
            "A200",
            "state_consistency",
            "warning",
            f"state consistency check could not run: {exc}",
            ".governance/index/",
            "repair index/current-state alignment before archive" if "archive" in str(exc).lower() else "",
        )


def _audit_archived_state_consistency(payload: dict, root: Path, change_id: str, archive_dir: Path) -> None:
    final_snapshot = _load_optional(archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml")
    receipt = _load_optional(archive_dir / "archive-receipt.yaml")
    passed = (
        final_snapshot.get("status") == "pass"
        and receipt.get("archive_executed") is True
        and receipt.get("change_id") == change_id
    )
    _add_check(
        payload,
        "A200",
        "state_consistency",
        "pass" if passed else "fail",
        "archived final state consistency passed" if passed else "archived final state consistency is missing or failed",
        str((archive_dir / "FINAL_STATE_CONSISTENCY_CHECK.yaml").relative_to(root)),
        "regenerate archive receipt and final state snapshot through canonical archive" if not passed else "",
    )


def _audit_step_outputs(payload: dict, change_dir: Path, manifest: dict, *, base_ref: str = ".governance/changes") -> None:
    current_step = _as_int(manifest.get("current_step"), default=0)
    for step in range(1, min(current_step, 9) + 1):
        md_path = change_dir / f"step-reports/step-{step}.md"
        yaml_path = change_dir / f"step-reports/step-{step}.yaml"
        has_report = _substantive_file(md_path) or _substantive_file(yaml_path)
        _add_check(
            payload,
            f"A3{step:02d}",
            f"step_{step}_output_contract",
            "pass" if has_report else "warning",
            f"Step {step} output {'is materialized' if has_report else 'is not materialized'}",
            f"{base_ref}/{manifest.get('change_id') or change_dir.name}/step-reports/step-{step}.md",
            "materialize the missing step report before final review/archive" if not has_report else "",
        )


def _audit_step_output_contract(payload: dict, change_dir: Path, manifest: dict, contract: dict, change_id: str, *, base_ref: str = ".governance/changes") -> None:
    try:
        from .step_output_contract import evaluate_step_output_contract

        results = evaluate_step_output_contract(change_dir, _as_int(manifest.get("current_step"), default=0))
    except Exception as exc:
        _add_check(
            payload,
            "A350",
            "step_output_contract",
            "warning",
            f"step output contract could not run: {exc}",
            f".governance/changes/{change_id}/",
            "repair step output contract evaluation before review/archive",
        )
        return
    strict = _baseline_required(manifest, contract) or (change_dir / "BASELINE_REVIEW.md").exists()
    for item in results:
        status = item.get("status") or "fail"
        if status == "fail" and not strict:
            status = "warning"
        _add_check(
            payload,
            f"A35{item.get('step')}",
            item.get("name", "step_required_output"),
            status,
            item.get("message", "step required output check"),
            f"{base_ref}/{change_id}/{item.get('selected_ref') or item.get('canonical') or ''}",
            "materialize the canonical required output; step report alone is not sufficient" if status == "fail" else "",
        )


def _audit_baseline(payload: dict, change_dir: Path, manifest: dict, contract: dict, gates: dict) -> None:
    baseline_path = change_dir / "BASELINE_REVIEW.md"
    baseline_required = _baseline_required(manifest, contract) or baseline_path.exists()
    if not baseline_required:
        _add_check(payload, "A400", "baseline_canonical_artifact", "warning", "canonical Step 5 baseline is not declared for this change", str(baseline_path))
        return
    if not _substantive_file(baseline_path):
        _add_check(payload, "A400", "baseline_canonical_artifact", "fail", "BASELINE_REVIEW.md is missing or empty", str(baseline_path), "create the canonical Step 5 baseline before Step 6")
        return
    text = baseline_path.read_text(encoding="utf-8")
    has_front_matter = "canonical_artifact: true" in text and "schema:" in text
    _add_check(
        payload,
        "A400",
        "baseline_canonical_artifact",
        "pass" if has_front_matter else "fail",
        "BASELINE_REVIEW.md declares canonical artifact front matter" if has_front_matter else "BASELINE_REVIEW.md lacks canonical artifact front matter",
        str(baseline_path),
        "add schema and canonical_artifact: true front matter" if not has_front_matter else "",
    )
    approval = _approval(gates, 5)
    approval_text = " ".join(str(approval.get(key) or "") for key in ("note", "evidence_ref", "approval_token"))
    approved_digest = _first_sha256(approval_text)
    baseline_digest = _sha256(baseline_path)
    bound = "BASELINE_REVIEW.md" in approval_text and approved_digest == baseline_digest
    _add_check(
        payload,
        "A401",
        "step5_baseline_approval_binding",
        "pass" if bound else "fail",
        "Step 5 approval binds the current baseline digest" if bound else "Step 5 approval does not bind the current baseline digest for BASELINE_REVIEW.md",
        str(change_dir / "human-gates.yaml"),
        f"record Step 5 approval text or evidence_ref that names BASELINE_REVIEW.md and sha256:{baseline_digest}" if not bound else "",
    )
    _audit_baseline_reference_digests(payload, change_dir, approval_text)


def _audit_baseline_reference_digests(payload: dict, change_dir: Path, approval_text: str) -> None:
    baseline = _load_optional(change_dir / "execution-baseline.yaml")
    refs = baseline.get("baseline") if isinstance(baseline, dict) else {}
    if not isinstance(refs, dict) or not refs:
        _add_check(payload, "A402", "baseline_reference_digests", "warning", "no execution-baseline digest map is available", str(change_dir / "execution-baseline.yaml"))
        return
    strict = (baseline.get("approval") or {}).get("state") == "approved" or "execution-baseline.yaml" in approval_text
    mismatches = []
    for item in refs.values():
        if not isinstance(item, dict) or not item.get("path") or not item.get("digest"):
            continue
        path = change_dir.parent.parent.parent / _normalize_relative_path(str(item["path"]))
        if not path.exists():
            mismatches.append(f"{item['path']} missing")
            continue
        actual = "sha256:" + _sha256(path)
        if actual != item.get("digest"):
            mismatches.append(str(item["path"]))
    status = "fail" if strict and mismatches else "warning" if mismatches else "pass"
    _add_check(
        payload,
        "A402",
        "baseline_reference_digests",
        status,
        f"baseline reference digest mismatches: {', '.join(mismatches)}" if mismatches else "baseline reference digests match tracked files",
        str(change_dir / "execution-baseline.yaml"),
        "renew Step 5 baseline approval after referenced artifacts change" if status == "fail" else "",
    )


def _audit_human_gate_reconciliation(payload: dict, change_dir: Path, bindings: dict, gates: dict) -> None:
    steps = bindings.get("steps", {}) if isinstance(bindings, dict) else {}
    approvals = gates.get("approvals", {}) if isinstance(gates, dict) else {}
    acknowledgements = gates.get("acknowledgements", []) if isinstance(gates, dict) else []
    ack_steps = {int(item.get("step")) for item in acknowledgements if isinstance(item, dict) and str(item.get("step")).isdigit()}
    missing = []
    for raw_step, binding in steps.items():
        if not isinstance(binding, dict) or not binding.get("human_gate"):
            continue
        try:
            step = int(str(raw_step).strip("'"))
        except ValueError:
            continue
        approval = approvals.get(step) or approvals.get(str(step)) or approvals.get(f"'{step}'")
        if step in ack_steps and not (isinstance(approval, dict) and approval.get("status") == "approved"):
            missing.append(step)
    _add_check(
        payload,
        "A450",
        "human_gate_reconciliation",
        "fail" if missing else "pass",
        f"acknowledgement exists without canonical approval for human gate steps: {', '.join(str(item) for item in missing)}" if missing else "human gate acknowledgements are reconciled with canonical approvals",
        str(change_dir / "human-gates.yaml"),
        "ask the human sponsor for explicit approval; do not convert acknowledgement into approval automatically" if missing else "",
    )


def _audit_writer_metadata(payload: dict, change_dir: Path, manifest: dict, contract: dict) -> None:
    strict = _baseline_required(manifest, contract) or (change_dir / "BASELINE_REVIEW.md").exists()
    required = {
        "human-gates.yaml": "warning",
        "verify.yaml": "fail" if strict else "warning",
        "review.yaml": "fail" if strict else "warning",
        "archive-receipt.yaml": "fail" if strict else "warning",
    }
    missing = []
    warning_missing = []
    for name, severity in required.items():
        path = change_dir / name
        if not path.exists():
            continue
        data = _load_optional(path)
        if not data:
            continue
        if name == "archive-receipt.yaml" and _canonical_archive_receipt(data):
            continue
        if not isinstance(data, dict) or not data.get("writer"):
            (missing if severity == "fail" else warning_missing).append(name)
    status = "fail" if missing else "warning" if warning_missing else "pass"
    message = "writer metadata exists on critical governance facts"
    if missing or warning_missing:
        message = "missing writer metadata: " + ", ".join(missing + warning_missing)
    _add_check(
        payload,
        "A460",
        "writer_metadata",
        status,
        message,
        str(change_dir),
        "regenerate critical governance facts through canonical writer commands" if status == "fail" else "",
    )


def _audit_canonical_artifacts(payload: dict, change_dir: Path, manifest: dict, contract: dict) -> None:
    strict = _baseline_required(manifest, contract) or (change_dir / "BASELINE_REVIEW.md").exists()
    issues = []
    for report_name in ("VERIFY_REPORT.md", "REVIEW_REPORT.md", "FINAL_ROUND_REPORT.md"):
        report = change_dir / report_name
        if not report.exists():
            continue
        if report_name == "FINAL_ROUND_REPORT.md" and _human_final_round_report(report, change_dir):
            continue
        front = _front_matter(report)
        source_name = front.get("source_facts")
        if front.get("canonical_artifact") != "true":
            issues.append(f"{report_name} lacks canonical_artifact front matter")
        if source_name:
            source = change_dir / source_name
            if not source.exists():
                issues.append(f"{report_name} source_facts missing: {source_name}")
            digest = front.get("source_digest")
            if digest and source.exists() and digest != "sha256:" + _sha256(source):
                issues.append(f"{report_name} source_digest mismatch")
    _add_check(
        payload,
        "A470",
        "canonical_artifact_consistency",
        "fail" if strict and issues else "warning" if issues else "pass",
        "; ".join(issues) if issues else "canonical Markdown artifacts are consistent with their structured source facts",
        str(change_dir),
        "regenerate canonical artifacts and structured facts from the same writer" if strict and issues else "",
    )


def _canonical_archive_receipt(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    traceability = data.get("traceability") or {}
    return (
        data.get("schema") == "archive-receipt/v1"
        and data.get("archive_executed") is True
        and isinstance(traceability, dict)
        and bool(traceability.get("final_round_report"))
        and bool(traceability.get("final_state_consistency"))
    )


def _human_final_round_report(report: Path, change_dir: Path) -> bool:
    text = report.read_text(encoding="utf-8")
    receipt = _load_optional(change_dir / "archive-receipt.yaml")
    traceability = receipt.get("traceability") or {}
    return (
        "# 最终闭环报告" in text
        and "## 初始需求" in text
        and "## 最终结论" in text
        and "## 四阶段九步过程简报" in text
        and "FINAL_ROUND_REPORT.md" in str(traceability.get("final_round_report", ""))
    )


def _audit_rule_sources(payload: dict, root: Path, change_dir: Path, change_id: str) -> None:
    rules = _collect_rule_sources(root, change_dir)
    malformed = [
        rule for rule in rules
        if not rule.get("applies_to_steps") or not rule.get("severity") or not rule.get("evidence_required") or not rule.get("fallback")
    ]
    _add_check(
        payload,
        "A480",
        "rule_sources",
        "fail" if malformed else "pass",
        f"rules missing required fields: {', '.join(str(rule.get('id') or rule.get('name') or '<unnamed>') for rule in malformed)}" if malformed else f"{len(rules)} governance rules are audit-ready",
        f".governance/changes/{change_id}/ and .governance/policies/",
        "declare applies_to_steps, severity, evidence_required, and fallback for every rule" if malformed else "",
    )


def _collect_rule_sources(root: Path, change_dir: Path) -> list[dict]:
    builtin = [
        {
            "id": "builtin-step-output-contract",
            "source": "builtin",
            "applies_to_steps": list(range(1, 10)),
            "severity": "blocking",
            "evidence_required": ["canonical_required_output"],
            "fallback": "halt_and_report",
        },
        {
            "id": "builtin-no-unresolved-bypass",
            "source": "builtin",
            "applies_to_steps": [7, 8, 9],
            "severity": "blocking",
            "evidence_required": ["flow_bypass_recovery"],
            "fallback": "halt_and_report",
        },
    ]
    loaded = list(builtin)
    for path in (root / ".governance/policies/rules.yaml", change_dir / "rules.yaml"):
        if path.exists():
            data = _load_optional(path)
            loaded.extend(list(data.get("rules") or []))
    adapter_path = root / ".governance/policies/skill-adapters.yaml"
    if adapter_path.exists():
        data = _load_optional(adapter_path)
        loaded.extend(list(data.get("rules") or data.get("adapters") or []))
    return loaded


def _audit_scope(payload: dict, change_dir: Path, contract: dict) -> None:
    manifest_path = change_dir / "evidence/changed-files-manifest.yaml"
    if not manifest_path.exists():
        _add_check(payload, "A500", "changed_files_scope", "warning", "changed files manifest is not present yet", str(manifest_path))
        return
    changed = _load_optional(manifest_path)
    files = list(changed.get("files") or changed.get("modified") or changed.get("created") or [])
    scope_in = list(contract.get("scope_in") or [])
    scope_out = list(contract.get("scope_out") or [])
    scope_approvals = _load_scope_expansion_approvals(change_dir)
    violations = [
        item
        for item in files
        if _outside_scope(str(item), scope_in, scope_out)
        and not _scope_violation_is_approved(str(item), scope_approvals)
    ]
    _add_check(
        payload,
        "A500",
        "changed_files_scope",
        "fail" if violations else "pass",
        f"scope violations: {', '.join(violations)}" if violations else "changed files are within declared scope",
        str(manifest_path),
        "move the change into scope or get explicit human approval to expand scope" if violations else "",
    )


def _load_scope_expansion_approvals(change_dir: Path) -> list[dict]:
    approvals: list[dict] = []
    evidence_path = change_dir / "evidence/scope-expansion-approval.yaml"
    if evidence_path.exists():
        data = _load_optional(evidence_path)
        if isinstance(data, dict):
            approvals.extend(list(data.get("approvals") or []))
            if data.get("approved_paths"):
                approvals.append(data)
    gates_path = change_dir / "human-gates.yaml"
    if gates_path.exists():
        gates = _load_optional(gates_path)
        if isinstance(gates, dict):
            approvals.extend(list(gates.get("scope_expansions") or gates.get("scope_expansion_approvals") or []))
    return approvals


def _scope_violation_is_approved(path: str, approvals: list[dict]) -> bool:
    from fnmatch import fnmatch

    normalized = _normalize_scope_path(path)
    for approval in approvals:
        if not isinstance(approval, dict):
            continue
        approved_by = str(approval.get("approved_by") or approval.get("actor") or "").strip()
        reason = str(approval.get("reason") or approval.get("human_request") or approval.get("approval_text") or "").strip()
        if not approved_by or not reason:
            continue
        for pattern in approval.get("approved_paths") or approval.get("paths") or []:
            candidate = _normalize_scope_path(str(pattern))
            if fnmatch(normalized, candidate) or (candidate.endswith("/**") and normalized.startswith(candidate[:-3].rstrip("/") + "/")):
                return True
    return False


def _audit_recovery(payload: dict, change_dir: Path, change_id: str) -> None:
    recovery_path = change_dir / "recovery/bypass-records.yaml"
    recovery = _load_optional(recovery_path)
    records = list(recovery.get("records") or []) if isinstance(recovery, dict) else []
    unresolved = [item for item in records if item.get("resolved") is not True]
    _add_check(
        payload,
        "A600",
        "flow_bypass_recovery",
        "fail" if unresolved else "pass",
        "unresolved flow bypass recovery records exist" if unresolved else "no unresolved flow bypass recovery records",
        f".governance/changes/{change_id}/recovery/bypass-records.yaml",
        "resolve or explicitly carry forward recovery records before review/archive" if unresolved else "",
    )


def _audit_reviewer_separation(payload: dict, bindings: dict, review: dict) -> None:
    steps = bindings.get("steps") if isinstance(bindings, dict) else {}
    if not isinstance(steps, dict):
        steps = {}
    step6 = steps.get(6) or steps.get("6") or {}
    executor = step6.get("owner")
    reviewers = [item.get("id") for item in review.get("reviewers", []) if isinstance(item, dict)]
    if not reviewers:
        _add_check(payload, "A700", "reviewer_independence", "warning", "no review decision has been recorded yet", "review.yaml")
        return
    self_reviewers = [item for item in reviewers if item and item == executor]
    _add_check(
        payload,
        "A700",
        "reviewer_independence",
        "fail" if self_reviewers else "pass",
        f"reviewer must differ from executor: {', '.join(self_reviewers)}" if self_reviewers else "reviewer is independent from Step 6 executor",
        "bindings.yaml/review.yaml",
        "assign an independent reviewer before approval" if self_reviewers else "",
    )


def _audit_review_closure(payload: dict, review: dict, gates: dict) -> None:
    if not review:
        _add_check(payload, "A800", "review_archive_gate", "warning", "review decision is not recorded yet", "review.yaml")
        return
    approved = review.get("decision", {}).get("status") == "approve"
    step8 = _approval(gates, 8).get("status") == "approved"
    step9 = _approval(gates, 9).get("status") == "approved"
    status = "pass" if approved and step8 and step9 else "warning"
    _add_check(
        payload,
        "A800",
        "review_archive_gate",
        status,
        "review and archive gates are approved" if status == "pass" else "review/archive human gates are not fully approved yet",
        "review.yaml/human-gates.yaml",
    )


def _finalize(payload: dict) -> dict:
    summary = {"pass": 0, "warning": 0, "fail": 0}
    for check in payload.get("checks") or []:
        summary[check.get("status", "fail")] = summary.get(check.get("status", "fail"), 0) + 1
    payload["summary"] = summary
    if summary.get("fail", 0):
        payload["status"] = "fail"
    elif summary.get("warning", 0):
        payload["status"] = "warning"
    else:
        payload["status"] = "pass"
    return payload


def _add_check(payload: dict, check_id: str, name: str, status: str, message: str, ref: str, required_action: str = "") -> None:
    payload.setdefault("checks", []).append({
        "id": check_id,
        "name": name,
        "status": status,
        "message": message,
        "ref": ref,
        "required_action": required_action,
    })


def _current_change_id(paths: GovernancePaths) -> str | None:
    try:
        current = read_current_change(paths.root)
    except Exception:
        return None
    nested = current.get("current_change")
    if not isinstance(nested, dict):
        nested = {}
    value = current.get("current_change_id") or nested.get("change_id")
    return str(value) if value else None


def _load_optional(path: Path) -> dict:
    return load_yaml(path) if path.exists() else {}


def _substantive_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8").strip()
    placeholders = {"", "todo", "tbd", "{}", "[]"}
    return text.lower() not in placeholders and len(text) >= 12


def _baseline_required(manifest: dict, contract: dict) -> bool:
    values = []
    values.extend(list(manifest.get("target_validation_objects") or []))
    values.extend(list(contract.get("validation_objects") or []))
    values.extend(list(contract.get("evidence_expectations", {}).get("required") or []))
    haystack = " ".join(str(item) for item in values).lower()
    return "baseline_review" in haystack or "baseline" in haystack


def _approval(gates: dict, step: int) -> dict:
    approvals = gates.get("approvals") if isinstance(gates, dict) else {}
    if not isinstance(approvals, dict):
        return {}
    approval = approvals.get(step) or approvals.get(str(step)) or approvals.get(f"'{step}'")
    return approval if isinstance(approval, dict) else {}


def _outside_scope(path: str, scope_in: list[str], scope_out: list[str]) -> bool:
    from fnmatch import fnmatch

    normalized = _normalize_scope_path(path)
    for pattern in scope_out:
        candidate = _normalize_scope_path(str(pattern))
        if fnmatch(normalized, candidate) or (candidate.endswith("/**") and normalized.startswith(candidate[:-3].rstrip("/") + "/")):
            return True
    if not scope_in:
        return False
    for pattern in scope_in:
        candidate = _normalize_scope_path(str(pattern))
        if fnmatch(normalized, candidate) or (candidate.endswith("/**") and normalized.startswith(candidate[:-3].rstrip("/") + "/")):
            return False
    return True


def _normalize_scope_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_relative_path(path: str) -> str:
    value = path.strip()
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _first_sha256(text: str) -> str:
    match = re.search(r"sha256:([a-fA-F0-9]{64})", text or "")
    return match.group(1).lower() if match else ""


def _front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    marker = text.find("\n---", 4)
    if marker == -1:
        return {}
    fields = {}
    for line in text[4:marker].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("'\"")
    return fields
