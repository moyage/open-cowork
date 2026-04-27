# v0.3.1 Release and Next Dogfood Round

Release: `0.3.1`
Date: 2026-04-27
Archived change: `v0.3.1-human-participation-runtime`

## Release Summary

v0.3.1 hardens the human participation runtime that was introduced in v0.3.0. The release focuses on real dogfood friction: new changes must visibly start from Step 1, `change prepare` must not imply hidden completion, status views should be usable by Agents when reporting to humans, review `revise` decisions must reopen a clear recovery loop, and independent review dispatch must leave runtime evidence rather than relying on narrative claims.

## Main Changes

- New change packages now default to Step 1 visibility instead of making Step 1-5 appear complete after preparation.
- Added human-facing intent, participants, change status, and last-archive status views.
- Step reports aggregate execution evidence, verification evidence, review runtime evidence, and independent reviewer invocation metadata.
- Added `review-revise` recovery through `ocw revise` and `revision-history.yaml`.
- Added default unstable/generated directory exclusions for `.git`, `.omx`, `.venv`, `dist`, `node_modules`, `.release`, `.governance/archive`, and `.governance/runtime`.
- Review decisions now carry runtime evidence for real local-agent dispatch, fallback, and failure transparency.
- Idle status can show the last archived closeout summary for humans and follow-up Agents.

## Release Verification

- `python3 -m unittest discover -s tests -v`: 180 tests OK.
- `./scripts/smoke-test.sh`: pass.
- `./bin/ocw version`: `open-cowork 0.3.1`.
- `./bin/ocw hygiene --format json`: `state_consistency.status = pass`.
- `git diff --check`: pass.
- `uv build --out-dir /tmp/open-cowork-dist-uv`: built `open_cowork-0.3.1.tar.gz` and `open_cowork-0.3.1-py3-none-any.whl`.

## Archive Evidence

- `.governance/archive/v0.3.1-human-participation-runtime/archive-receipt.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/FINAL_STATE_CONSISTENCY_CHECK.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/review.yaml`
- `.governance/archive/v0.3.1-human-participation-runtime/step-reports/step-9.yaml`
- `docs/reports/2026-04-27-v031-final-retrospective-and-closeout-report.md`

## Independent Review Evidence

- Hermes was invoked as the primary reviewer but failed with provider HTTP 403 quota / pre-consume token failure.
- OOSO/OMOC was invoked as the real local fallback reviewer after human-approved reviewer mismatch bypass.
- OOSO initial review requested `revise`; revision round 1 was completed; OOSO rereview approved the change.
- Reviewer mismatch bypass and runtime evidence are recorded in `human-gates.yaml`, `review.yaml`, and final consistency summary.

## Next Dogfood Focus

Ask team members to test v0.3.1 in real personal-domain Agent workflows and collect feedback on:

- Whether a new change clearly starts at Step 1 before prepare / execution.
- Whether `intent status`, `participants list`, `change status`, and `status --last-archive` are enough for Agents to report progress without exposing CLI-first details to humans.
- Whether review `revise` and subsequent rerun/rereview feel recoverable rather than confusing.
- Whether real local independent reviewer dispatch evidence is easy to inspect.
- Whether archive closeout and idle status give enough context after session compression.
- Whether remaining report wording or snapshot artifacts still create ambiguity after Step 9.

