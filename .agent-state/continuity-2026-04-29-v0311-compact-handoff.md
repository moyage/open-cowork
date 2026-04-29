# open-cowork v0.3.11 Compact Handoff

generated_at: 2026-04-29 15:57:28 HKT

## Current State

- Repository: `/Users/mlabs/Programs/open-cowork`
- Active lean round: `v0311-dogfood-resume`
- Lifecycle: `v0311-dogfood-resume-closeout-complete`
- `ocw resume`: `continue-active-round`, phase `closeout`, `waiting_on: none`
- Next recommended round: v0.3.11 release preparation

## What Was Completed

1. Recovered failed session `019dd810-893c-7d00-ac9a-bd6c0d34a109` with `/Users/mlabs/.codex/bin/codex-session-recover`.
2. Continued from the prior point: lean-only `ocw resume` test had just gone green.
3. Dogfooded lean governance in this repository:
   - `.governance/state.yaml`
   - `.governance/evidence.yaml`
   - `.governance/ledger.yaml`
   - `.governance/rules.yaml`
4. Completed `v0311-dogfood-resume` closeout:
   - verify result: `.agent-state/tasks/v0311-dogfood-resume/verify-result.md`
   - Hermes review: `.agent-state/tasks/v0311-dogfood-resume/hermes-review.md`
   - closeout: `.agent-state/tasks/v0311-dogfood-resume/closeout.md`

## Verification Evidence

- `validate_lean_documents('.')`: PASS
- `PYTHONPATH=src python3 -m governance.cli --root . resume`: PASS
- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_v0311_*.py'`: PASS, 32 tests
- `PYTHONPATH=src python3 -m unittest discover -s tests`: PASS, 279 tests
- Real local Hermes review: `decision: approve`, session `20260429_154535_fc72df`

## Important Scope Notes

- No staging, commit, tag, push, PR, or package release was performed.
- Existing worktree is intentionally dirty from the v0.3.11 implementation/doc batches.
- Do not revert unrelated changes. Treat existing modifications as prior task output unless explicitly asked.
- Final review cannot be self-approved by Codex; use real local Hermes or equivalent local Agent for future final reviews.
- For future code/project file edits in this repo, run `ocw resume` first.

## Known Non-blocking Risks

- `_is_lean_only()` currently uses a simple discriminator: `.governance/state.yaml` exists and legacy `.governance/index/current-change.yaml` does not. Future mixed-layout migrations may need sharper handling.
- `format_project_activation()` would print both legacy and lean sections if a future payload incorrectly contained both; current paths are mutually exclusive.

## Next Best Step

Start a new round for v0.3.11 release preparation:

1. Run `ocw resume`.
2. Create an execution contract for release prep.
3. Audit final diff and file scope.
4. Check version/package metadata and docs/changelog needs.
5. Run targeted and full tests.
6. Request real local Hermes review.
7. Only then decide whether to tag, publish, push, or open PR.
