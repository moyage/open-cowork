# v0.3.0 Release and Next Dogfood Round

Release: `0.3.0`
Date: 2026-04-26
Archived change: `v0.3-human-participation-closeout-readability`

## Release Summary

v0.3.0 turns the v0.2.9 hard-gate foundation into a human-visible collaboration experience. The release keeps the standard Step 1-9 runtime flow as the canonical protocol, uses the traditional 4 human phases only as explanatory mapping, and makes step boundaries, owners, gate semantics, review decisions, archive closeout, and Agent actions easier for humans to inspect.

## Main Changes

- `change prepare` no longer implies Step 1-5 completion.
- Step reports now expose `framework_controls`, `agent_actions_done`, `agent_actions_expected`, human decisions, and short approve/revise/reject options.
- Status snapshots now distinguish `gate_type`, `gate_state`, and `approval_state`.
- Step 5 / Step 8 / Step 9 approvals are visible in report, review, archive, and final consistency artifacts.
- Reviewer mismatch bypass requires a human-readable reason, recorder, and evidence reference.
- Idle current-state keeps a human-readable Chinese summary plus the `lifecycle: idle` machine anchor.

## Release Verification

- `PYTHONPATH=tests python3 -m unittest discover -s tests -v`: 172 tests OK.
- `./scripts/smoke-test.sh`: pass.
- `bin/ocw hygiene --format json`: `state_consistency.status = pass`.
- `git diff --check`: pass.
- `uv build --out-dir /tmp/open-cowork-dist-uv`: built `open_cowork-0.3.0.tar.gz` and `open_cowork-0.3.0-py3-none-any.whl`.

## Archive Evidence

- `.governance/archive/v0.3-human-participation-closeout-readability/archive-receipt.yaml`
- `.governance/archive/v0.3-human-participation-closeout-readability/FINAL_STATE_CONSISTENCY_CHECK.yaml`
- `.governance/archive/v0.3-human-participation-closeout-readability/step-reports/step-9.yaml`
- `docs/reports/2026-04-26-v030-final-retrospective-and-closeout-report.md`

## Next Dogfood Focus

Ask team members to test v0.3.0 in real personal-domain Agent workflows and collect feedback on:

- Whether Step 1-9 boundaries are clear without requiring humans to inspect YAML.
- Whether the short approve/revise/reject confirmation model reduces ambiguity.
- Whether `ocw status` and `.governance/current-state.md` give enough context after session compression.
- Whether review/archive closeout evidence is easy to inspect.
- Whether any remaining CLI-first friction still pushes humans to remember internal commands.
