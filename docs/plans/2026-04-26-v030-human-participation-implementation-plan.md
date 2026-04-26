# V0.3 Human Participation and Closeout Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement V0.3 so open-cowork becomes human-visible and human-confirmed at decision points, while preserving the standard 9-step runtime flow and the V0.2.9 hard gates.

**Architecture:** Reuse the current file-backed governance modules and CLI. Add human-readable output, stronger provenance, and consolidated closeout traces without adding a dashboard or external service.

**Tech Stack:** Python standard library, existing `governance` package, `unittest`, shell smoke test.

---

## Normative Flow Guardrail

The implementation must not introduce a parallel lifecycle name such as "9-step human flow". The only lifecycle is the standard 9-step runtime flow defined in `docs/specs/07-standard-9-step-runtime-flow.md`.

Traditional human-facing mapping:

- Step 1-2: requirements intake and clarification
- Step 3: architecture / solution design
- Step 4-5: implementation package preparation and role assignment
- Step 6: controlled development / execution
- Step 7: testing and verification
- Step 8: review and acceptance
- Step 9: archive and maintenance handoff

`ocw change prepare` may create artifacts needed by later steps, but it must not imply that Step 1-5 are complete. V0.3 should add tests for this distinction.

## File Map

- Modify: `src/governance/agent_adoption.py` for adoption/onboarding human gate guidance.
- Modify: `src/governance/cli.py` for parser options and human-format output.
- Modify: `src/governance/change_prepare.py` or current-state projection code if prepare still reports Step 5 as the active human process state.
- Modify: `src/governance/intent.py` for confirmation provenance.
- Modify: `src/governance/step_report.py` for Step 1 clarification fields, `framework_controls`, `agent_actions`, and human rendering.
- Modify: `src/governance/step_matrix.py` for approval state semantics and status output.
- Modify: `src/governance/runtime_status.py` only if runtime projections expose approval state.
- Modify: `src/governance/review.py` for Step 8 approval trace and bypass requirements.
- Modify: `src/governance/archive.py` for final consistency gate summary.
- Modify: `src/governance/human_gates.py` only if a reusable approval/bypass reference helper is needed.
- Modify: `scripts/smoke-test.sh` to cover V0.3 human trace behavior.
- Create: `tests/test_v030.py` for all V0.3 regression coverage.
- Modify: `docs/getting-started.md`, `docs/agent-adoption.md`, `docs/README.md`, `README.md`, and `CHANGELOG.md` when release implementation is complete.

## Task 1: Standard Flow Terminology and Prepare-State Separation

**Files:**

- Create: `tests/test_v030.py`
- Modify: `src/governance/change_prepare.py`
- Modify: `src/governance/current_state.py`
- Modify: `src/governance/step_matrix.py`
- Modify: `src/governance/cli.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove `ocw change prepare` does not mark Step 1-5 as completed and does not describe the process as a separate human flow.

Expected assertions:

```python
self.assertIn("current_step: 1", current_change_text)
self.assertIn("completed_steps: none", status_output)
self.assertNotIn("9-step human flow", output.lower())
self.assertIn("standard 9-step runtime flow", output.lower())
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 -v
```

Expected: FAIL until prepare-state projection is corrected.

- [ ] **Step 3: Implement prepare-state separation**

Keep prepared artifacts visible, but model them as intake/preparation facts for Step 1 rather than completed Step 1-5 progress. Current status after prepare should guide the Agent to Step 1 input intake and problem framing.

- [ ] **Step 4: Run targeted tests**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 -v
```

Expected: PASS for terminology and prepare-state separation tests.

## Task 2: Entry Participation Prompts

**Files:**

- Create: `tests/test_v030.py`
- Modify: `src/governance/agent_adoption.py`
- Modify: `src/governance/cli.py`

- [ ] **Step 1: Write failing tests for adoption and onboarding gate guidance**

Add to `tests/test_v030.py`:

```python
from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from governance.agent_adoption import build_adoption_plan
from governance.cli import main


class V030HumanParticipationTests(unittest.TestCase):
    def test_adoption_plan_mentions_step5_step8_and_step9_human_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["--root", str(root), "init"])
            plan = build_adoption_plan(root, target=root, goal="Improve human participation")

            actions = "\n".join(plan["human_control_baseline_next_actions"])
            self.assertIn("Step 5", actions)
            self.assertIn("Step 8", actions)
            self.assertIn("Step 9", actions)
            self.assertIn("review", actions.lower())
            self.assertIn("archive", actions.lower())

    def test_onboard_output_surfaces_role_matrix_and_gate_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root),
                    "onboard",
                    "--target", str(root),
                    "--mode", "quickstart",
                    "--yes",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("owner matrix", output.lower())
            self.assertIn("Step 8", output)
            self.assertIn("Step 9", output)
            self.assertIn("human gate", output.lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030.V030HumanParticipationTests.test_adoption_plan_mentions_step5_step8_and_step9_human_gates tests.test_v030.V030HumanParticipationTests.test_onboard_output_surfaces_role_matrix_and_gate_confirmation -v
```

Expected: FAIL because current outputs do not mention the full Step 8/9 gate path or owner matrix.

- [ ] **Step 3: Implement adoption/onboarding text**

Update `src/governance/agent_adoption.py` so `human_control_baseline_next_actions` includes:

```python
"Confirm the 9-step owner / assistant / reviewer / human gate matrix with the human sponsor.",
"Record Step 5 approval before execution.",
"Pause for Step 8 human approval before review decision.",
"Pause for Step 9 human approval before archive closeout.",
```

Update onboarding output in `src/governance/cli.py` so quickstart text includes a compact owner matrix and tells the Agent to ask the human to confirm participants and gates.

- [ ] **Step 4: Run targeted tests**

Run the command from Step 2 again.

Expected: PASS.

## Task 3: Step 1 Clarification and Confirmation Provenance

**Files:**

- Modify: `tests/test_v030.py`
- Modify: `src/governance/intent.py`
- Modify: `src/governance/step_report.py`
- Modify: `src/governance/cli.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_v030.py`:

```python
    def test_step1_report_contains_requirements_clarification_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_id = "CHG-STEP1"
            main(["--root", str(root), "change", "create", change_id, "--title", "Step 1"])
            main([
                "--root", str(root), "change", "prepare", change_id,
                "--goal", "Clarify requirements",
                "--scope-in", "src/**",
                "--scope-in", "tests/**",
            ])
            main([
                "--root", str(root), "intent", "capture",
                "--change-id", change_id,
                "--project-intent", "Improve human participation",
                "--acceptance", "Human can confirm Step 1 summary",
                "--risk", "Ambiguous requirements",
            ])
            main(["--root", str(root), "step", "report", "--change-id", change_id, "--step", "1"])
            report = (root / ".governance/changes/CHG-STEP1/step-reports/step-1.md").read_text(encoding="utf-8")
            self.assertIn("Requirements source", report)
            self.assertIn("Requirement list", report)
            self.assertIn("Non-goals", report)
            self.assertIn("Open questions", report)

    def test_intent_confirm_records_recorded_by_evidence_ref_and_confirmation_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_id = "CHG-INTENT-PROV"
            main(["--root", str(root), "change", "create", change_id, "--title", "Intent provenance"])
            main([
                "--root", str(root), "change", "prepare", change_id,
                "--goal", "Record provenance",
                "--scope-in", "src/**",
            ])
            main([
                "--root", str(root), "intent", "capture",
                "--change-id", change_id,
                "--project-intent", "Record provenance",
            ])
            main([
                "--root", str(root), "intent", "confirm",
                "--change-id", change_id,
                "--confirmed-by", "human-sponsor",
                "--recorded-by", "orchestrator-agent",
                "--evidence-ref", "docs/reports/step1.md",
                "--confirmation-mode", "observed-human-approval",
            ])
            payload = (root / ".governance/changes/CHG-INTENT-PROV/intent-confirmation.yaml").read_text(encoding="utf-8")
            self.assertIn("recorded_by: orchestrator-agent", payload)
            self.assertIn("evidence_ref: docs/reports/step1.md", payload)
            self.assertIn("confirmation_mode: observed-human-approval", payload)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030.V030HumanParticipationTests.test_step1_report_contains_requirements_clarification_fields tests.test_v030.V030HumanParticipationTests.test_intent_confirm_records_recorded_by_evidence_ref_and_confirmation_mode -v
```

Expected: FAIL because fields/options do not exist yet.

- [ ] **Step 3: Implement provenance and Step 1 fields**

Add parser options to intent confirm in `src/governance/cli.py`:

```python
--recorded-by
--evidence-ref
--confirmation-mode
```

Store them under `human_confirmation` in `src/governance/intent.py`.

Update `src/governance/step_report.py` so Step 1 markdown includes the required clarification sections.

- [ ] **Step 4: Run targeted tests**

Run the command from Step 2 again.

Expected: PASS.

## Task 4: Human Step Report Format and Control Separation

**Files:**

- Modify: `tests/test_v030.py`
- Modify: `src/governance/step_report.py`
- Modify: `src/governance/cli.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_v030.py`:

```python
    def test_step_report_human_format_and_control_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            change_id = "CHG-HUMAN-REPORT"
            main(["--root", str(root), "change", "create", change_id, "--title", "Human report"])
            main([
                "--root", str(root), "change", "prepare", change_id,
                "--goal", "Human report",
                "--scope-in", "src/**",
            ])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([
                    "--root", str(root), "step", "report",
                    "--change-id", change_id,
                    "--step", "5",
                    "--format", "human",
                ])
            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Framework controls", output)
            self.assertIn("Agent actions", output)
            self.assertIn("Human decision", output)
            yaml_text = (root / ".governance/changes/CHG-HUMAN-REPORT/step-reports/step-5.yaml").read_text(encoding="utf-8")
            self.assertIn("framework_controls:", yaml_text)
            self.assertIn("agent_actions:", yaml_text)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030.V030HumanParticipationTests.test_step_report_human_format_and_control_separation -v
```

Expected: FAIL because `--format human` and fields are missing.

- [ ] **Step 3: Implement report fields and human renderer**

Add `framework_controls` and `agent_actions` to report payloads. Add `human` as an accepted step report format in `src/governance/cli.py`. Implement a human renderer in `src/governance/step_report.py` that prints the same core sections as markdown without YAML syntax.

- [ ] **Step 4: Run targeted test**

Run the command from Step 2 again.

Expected: PASS.

## Task 5: Status Approval Semantics and Idle Closeout

**Files:**

- Modify: `tests/test_v030.py`
- Modify: `src/governance/step_matrix.py`
- Modify: `src/governance/cli.py`
- Modify: `src/governance/runtime_status.py` if projections include approval state

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
self.assertIn("approval=not-required", output)
self.assertIn("approval=required-pending", output)
self.assertNotIn("Step 1: Clarify the goal | status=completed | approval=pending", output)
```

Add an archive-flow test that calls `ocw status` after archive and asserts:

```python
self.assertIn("Last archived change", output)
self.assertIn("9-step closeout", output)
self.assertIn("review-approved", output)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 -v
```

Expected: FAIL on the new status assertions.

- [ ] **Step 3: Implement approval states and idle closeout**

Update `_step_progress` in `src/governance/step_matrix.py` so approval state is derived from binding human gate plus approval/bypass records. Add idle status handling in CLI or step matrix to read the last archive from `.governance/index/maintenance-status.yaml` and summarize archive receipt/review/final step report.

- [ ] **Step 4: Run targeted tests**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 -v
```

Expected: PASS for status-related tests.

## Task 6: Review Trace, Final Gate Summary, and Bypass Hardening

**Files:**

- Modify: `tests/test_v030.py`
- Modify: `src/governance/review.py`
- Modify: `src/governance/archive.py`
- Modify: `src/governance/human_gates.py`
- Modify: `src/governance/cli.py`
- Modify: `scripts/smoke-test.sh`

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
self.assertIn("human_gate_ref", review_yaml_text)
self.assertIn("step8", review_yaml_text)
self.assertIn("human_gate_summary:", final_consistency_text)
self.assertIn("step5:", final_consistency_text)
self.assertIn("step8:", final_consistency_text)
self.assertIn("step9:", final_consistency_text)
```

Add bypass validation tests:

```python
exit_code = main([
    "--root", str(root), "review",
    "--change-id", change_id,
    "--decision", "approve",
    "--reviewer", "wrong-reviewer",
    "--allow-reviewer-mismatch",
])
self.assertNotEqual(exit_code, 0)
self.assertIn("reason", stdout.getvalue().lower())
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 -v
```

Expected: FAIL on review trace, final consistency, and bypass validation.

- [ ] **Step 3: Implement trace and bypass requirements**

Add CLI options:

```text
--bypass-reason
--bypass-recorded-by
--bypass-evidence-ref
```

Require them when `--allow-reviewer-mismatch` is used. Store bypass details in `human-gates.yaml` and `review.yaml`. Add Step 8 human gate ref to normal `review.yaml`. Add gate summary to archive final consistency.

- [ ] **Step 4: Update smoke test**

Extend `scripts/smoke-test.sh` to assert review trace and final consistency gate summary after archive.

- [ ] **Step 5: Run targeted tests**

Run:

```bash
PYTHONPATH=tests python3 -m unittest tests.test_v030 tests.test_v029 -v
```

Expected: PASS.

## Task 7: Documentation and Release Readiness

**Files:**

- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/agent-adoption.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Update docs**

Document the V0.3 behavior:

- Agent-first means Agent-operated, human-visible, and human-confirmed at decision points.
- Step 1 requirements clarification.
- Step report human format.
- Status approval states.
- Idle closeout.
- Review trace and final consistency gate summary.
- Reviewer mismatch bypass risk acceptance.

- [ ] **Step 2: Run verification**

Run:

```bash
PYTHONPATH=tests python3 -m unittest discover -s tests -v
./scripts/smoke-test.sh
bin/ocw contract validate --change-id v0.3-human-participation-closeout-readability
bin/ocw hygiene --format json
```

Expected: all pass; hygiene `state_consistency.status` is `pass`.

- [ ] **Step 3: Record governance evidence**

Record changed files manifest, command output summary, and verification evidence under `.governance/changes/v0.3-human-participation-closeout-readability/evidence/`.

- [ ] **Step 4: Request independent review**

Use a reviewer distinct from the executor. Do not archive until review approves and Step 9 human approval is recorded.
