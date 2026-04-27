# V0.3.5-V0.3.6 Audit Findings

Audit resumed after session interruption `019dcecc-972c-7ba3-abaf-ba5da47813e6`.

## Scope

- Baseline: `v0.3.4`
- Reviewed target: `HEAD` / `v0.3.6` (`9525c5a`)
- Goal: release-quality audit for v0.3.5-v0.3.6 external-agent updates.

## Verification

- `python3 -m unittest discover -s tests`: pass, 206 tests.
- `./scripts/smoke-test.sh`: pass, 206 tests plus smoke flow.
- `python3 -m build`: not run, local environment is missing the `build` package (`No module named build`).

## Findings

### P1: `ocw resume` ignores a single active change when `current-change.yaml` is idle or stale

Status: resolved after follow-up implementation.

Evidence:

- File: `src/governance/activation.py`
- Lines: 39-74

`build_project_activation()` loads `.governance/index/active-changes.yaml`, but only uses that list when there are multiple active changes. If there is exactly one active change and `.governance/index/current-change.yaml` is idle, stale, or rebuilt as a local pointer, `ocw resume` reports `open-new-change` while still listing the active change.

This conflicts with the v0.3.6 design that `current-change.yaml` is not the team-authoritative source and active changes can be rebuilt from change manifests.

Minimal reproduction:

```sh
tmp=$(mktemp -d)
PYTHONPATH=src python3 -m governance.cli --root "$tmp" init >/dev/null
PYTHONPATH=src python3 -m governance.cli --root "$tmp" change create REQ-ONLY --title One >/dev/null
PYTHONPATH=src python3 -m governance.cli --root "$tmp" change prepare REQ-ONLY --goal One --active-policy force >/dev/null
PYTHONPATH=src python3 - <<'PY' "$tmp"
from pathlib import Path
import sys
from governance.simple_yaml import write_yaml
root=Path(sys.argv[1])
write_yaml(root/'.governance/index/current-change.yaml', {'schema':'current-change/v1','status':'idle','current_change':None,'note':'simulated lost pointer'})
PY
PYTHONPATH=src python3 -m governance.cli --root "$tmp" resume
```

Observed output includes:

```text
recommended_mode: open-new-change
Active changes:
- REQ-ONLY status=step1-ready step=1 title=One
```

Expected output should be `continue-active-change` for `REQ-ONLY`, or an explicit recovery mode that does not ask the human to open a new change.

Resolution:

- `build_project_activation()` now routes `len(active_changes) == 1` to `_activation_for_change()` when the current pointer is idle or terminal.
- Regression coverage added in `tests/test_v036.py::test_resume_uses_single_indexed_active_change_when_current_pointer_is_idle`.

### P2: The repository's own project handoff files still describe pre-v0.3.6 activation semantics

Status: resolved after follow-up implementation.

Original evidence before resolution:

- `.governance/AGENTS.md` line 7 pointed to the legacy current-state projection.
- `.governance/agent-entry.md` lines 9-13 described generic activation instead of the v0.3.6 deterministic `ocw resume` trigger.
- `.governance/agent-playbook.md` line 10 referenced the legacy current-state projection.

Generated target-project templates were updated, but this repository's checked-in governance handoff files were not fully migrated to the v0.3.6 semantics. That creates a self-dogfood drift: a new Agent entering this repo may follow stale activation instructions even though the release docs and generated templates say to use `ocw resume` and `.governance/local/current-state.md`.

Resolution:

- Repository-level `.governance/AGENTS.md`, `.governance/agent-entry.md`, and `.governance/agent-playbook.md` now use `ocw resume` and `.governance/local/current-state.md`.
- Repository-level `.governance/.gitignore` now ignores local projection paths.
- `resume --list` is now list-only and does not write activation/current-state projection files.
- Regression coverage added in `tests/test_v036.py::test_resume_list_is_list_only_and_does_not_write_activation_projection`.

## Dogfood Feedback Follow-up

Additional team feedback checked against:

- `/Users/mlabs/Programs/xsearch/docs/open-cowork/OPEN_COWORK_V033_DOGFOOD_REPORT_ZH.md`

Resolution summary:

- Step report fact-source merge is complete: intent-confirmation remains visible, but empty intent scope / acceptance now falls back to contract scope / verification checks and records `merged_from`.
- Step 9 closeout report now includes archive preview files and carry-forward items from review followups / archive residual followups.
- Long reviewer runs now have a first-class `review-invocation.yaml` heartbeat record, exposed through Step 8 report artifact summary.

## Release Gate

Recommendation: pass for deterministic resume, merge-safe governance, and xSearch v0.3.3 dogfood feedback closure after the follow-up fixes.

Fresh verification:

- `python3 -m unittest discover -s tests`: pass, 210 tests.
- `./scripts/smoke-test.sh`: pass.
- `python3 -m build`: pass, built `open_cowork-0.3.6.tar.gz` and `open_cowork-0.3.6-py3-none-any.whl`.
