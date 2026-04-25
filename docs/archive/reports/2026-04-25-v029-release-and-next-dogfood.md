# v0.2.9 Release and Next Dogfood Round

Date: 2026-04-25
Release: `0.2.9`

## Release Summary

v0.2.9 closes the review/archive layer of the v0.2.8 human-gate model. The release makes Step 8 review approval and Step 9 archive approval explicit gates, blocks reviewer mismatch by default, records approval provenance, and gives humans a clearer 9-step status table.

## What Changed

- Step 8 human approval is required before `ocw review`.
- Step 9 human approval is required before `ocw archive`.
- Reviewer mismatch blocks review unless an explicit audited bypass is requested.
- Approval records can include `recorded_by` and `evidence_ref`.
- Archive receipts trace the final Step 9 report.
- `ocw step report` text output includes inputs, outputs, done criteria, and participant responsibilities.
- `ocw status` includes a 9-step progress table with approval status.
- Smoke and regression tests cover the v0.2.9 gate closure flow.

## Independent Review

The local personal-domain Hermes Agent reviewed the change.

- First review decision: `revise`
- Re-review decision: `approve`
- Final critical findings: none
- Final important findings: none
- Final minor findings: none

The review artifacts are stored in the v0.2.9 change package evidence.

## Verification

Release verification before archive:

- `PYTHONPATH=tests python3 -m unittest discover -s tests -v`
- `./scripts/smoke-test.sh`
- `bin/ocw contract validate --change-id v0.2.9-review-archive-gate-closure`
- `bin/ocw status`

## Next Dogfood Round

Ask team members to test v0.2.9 in real personal-domain Agent workflows and collect feedback on:

- Whether Step 8 and Step 9 gates feel visible without becoming noisy.
- Whether reviewer mismatch blocking is understandable and recoverable.
- Whether `ocw status` is enough for a human to know the current phase, owner, blocker, next decision, and approval state.
- Whether approval provenance is sufficient for handoff and audit.
- Whether archive receipts and Step 9 traceability make round close easier to trust.

Feedback should be collected as concrete observations with command output, screenshots or copied terminal snippets where useful, and the exact project context in which the issue appeared.
