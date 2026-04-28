# v0.3.10 governance enforcement

v0.3.10 adds an enforcement layer around the existing 9-step protocol. The goal is to make governance facts auditable before agents mutate project files, verify results, record review, or archive a change.

## Required outputs

Each step has a required output contract. Step reports summarize these outputs, but they do not replace them.

| Step | Required output |
| --- | --- |
| 1 | `intent-confirmation.yaml`, `INTENT_CONFIRMATION.md`, or `intent.md` |
| 2 | `requirements.md` |
| 3 | `design.md` |
| 4 | `tasks.md` |
| 5 | `BASELINE_REVIEW.md` |
| 6 | `evidence/execution-summary.yaml` |
| 7 | `VERIFY_REPORT.md` and `verify.yaml` |
| 8 | `REVIEW_REPORT.md` and `review.yaml` |
| 9 | `FINAL_ROUND_REPORT.md` and archive receipt facts |

The audit layer treats missing, empty, or template-like required output as a fail-level finding. Step 7 and Step 8 canonical Markdown reports are generated from the same writer path as their structured YAML facts.

## Audit gates

`ocw audit` emits machine-readable JSON/YAML or human-readable text. It checks required files, state consistency, required outputs, Step 5 baseline binding, human gate reconciliation, writer metadata, canonical artifact/source consistency, rule source validity, changed-file scope, flow-bypass recovery, reviewer independence, and review/archive closure.

Preflight, verify, review, and archive use gate-specific audit filtering:

- Preflight and verify block on fail-level findings that prove the baseline, required package files, human gate reconciliation, rule source, scope, or recovery state is unsafe.
- Review blocks on the same governance authority failures, writer metadata failures, and reviewer independence failures, while leaving state consistency to the prior verify step.
- Archive blocks on any fail-level audit result.

## Canonical artifacts

Human-facing approvals and reviews should point at canonical Markdown artifacts with machine-readable front matter. YAML remains the structured fact store for compatibility, but it is not the main human review surface.

The Step 5 approval must bind `BASELINE_REVIEW.md` and its current digest. Step 7 and Step 8 produce `VERIFY_REPORT.md` and `REVIEW_REPORT.md` from the same writer path as `verify.yaml` and `review.yaml`; when a Markdown artifact declares `source_digest`, audit compares it against the structured source fact.

Critical governance facts should carry writer metadata. `human-gates.yaml` is warning-level during migration, while handwritten `verify.yaml`, `review.yaml`, and archive receipt facts are fail-level because they can bypass canonical commands.

## Human gates

Acknowledgement is not approval. When bindings or role configuration make a step a human gate, audit compares `human-gates.yaml` acknowledgements with canonical approvals. If an acknowledgement exists without a matching approval, audit reports `gate_reconciliation_required` semantics and blocks later guarded transitions until the human sponsor explicitly approves.

## Rule sources

The enforcement layer has a small built-in rule pack and can load project policy from `.governance/policies/rules.yaml`, change-local `rules.yaml`, and auditable skill adapter declarations. Every rule must declare `applies_to_steps`, `severity`, `evidence_required`, and `fallback`; malformed rules are fail-level because Step 7/8/9 cannot decide whether to pass, warn, or block without those fields.

## Recovery

Flow bypass records are exceptional recovery facts, not normal evidence. Unresolved bypass records keep audit in a fail state and block archive.
