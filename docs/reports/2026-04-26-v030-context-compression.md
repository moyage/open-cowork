# V0.3 Preparation Context Compression

Date: 2026-04-26
Repository: `/Users/mlabs/Programs/open-cowork`
Current baseline: `v0.2.9` at commit `90fa288`

This file is the compact continuation context for the V0.3 preparation round. It exists to reduce context pressure and preserve the decision trail if the working conversation is compressed again.

## Baseline Facts

- `v0.2.9` is released locally and tagged as `v0.2.9`.
- The release change `v0.2.9-review-archive-gate-closure` is archived.
- The repository was clean before V0.3 preparation started.
- Fresh verification after release passed:
  - `PYTHONPATH=tests python3 -m unittest discover -s tests -v`
  - `./scripts/smoke-test.sh`
  - `bin/ocw contract validate --change-id v0.2.9-review-archive-gate-closure`
  - `bin/ocw hygiene --format json`
- The team dogfood report is external to this repository:
  - `/Users/mlabs/Programs/xsearch/docs/OPEN_COWORK_V029_DOGFOOD_REPORT_ZH.md`

## V0.2.9 Honest Acceptance

V0.2.9 achieved the narrow hard-gate engineering goals:

- reviewer mismatch is blocked by default;
- Step 8 approval is required before review;
- Step 9 approval is required before archive;
- Step 9 report is finalized after archive;
- `change prepare` mentions Step 5 approval;
- active `status` shows a 9-step table;
- approval records include `recorded_by` and `evidence_ref`.

V0.2.9 did not fully achieve the broader iteration direction:

- human participation is still mostly mediated by Agent narration;
- onboarding and adoption output still under-explain Step 8/9 gates;
- Step 1 is not yet a true requirements clarification and confirmation interaction;
- `step report` is still not a strong human-facing interface;
- audit facts remain split across multiple files;
- framework controls and Agent actions are not clearly separated in each step report.

## Team Feedback To Carry Forward

V0.3 must treat "Agent-first" as "Agent-operated, human-visible, human-confirmed at decision points", not "Agent-only behind the scenes".

Required direction:

1. Show a role and owner matrix during onboarding/adoption.
2. Make Step 1 a real requirements clarification and confirmation stage.
3. Make every step report include human-facing summaries, framework controls, and Agent actions.
4. Make human gates default-pause moments with concrete decision text and evidence.
5. Fix approval semantics in status output.
6. Show last archived closeout status when the project is idle.
7. Put Step 8 approval trace in `review.yaml`.
8. Put Step 5/8/9 approval summary in final consistency output.
9. Make reviewer mismatch bypass require reason, recorded-by, and evidence.
10. Update docs and tests so the behavior is not just aspirational.

## Normative Process Terms

- The framework has a fixed **standard 9-step runtime flow**, defined by `docs/specs/07-standard-9-step-runtime-flow.md`.
- The traditional human-facing phase mapping is:
  - Step 1-2: requirements intake and clarification
  - Step 3: architecture / solution design
  - Step 4-5: implementation package preparation and role assignment
  - Step 6: controlled development / execution
  - Step 7: testing and verification
  - Step 8: review and acceptance
  - Step 9: archive and maintenance handoff
- "Pre-Step 1" is not a framework step. It only means iteration intake materials have been gathered before the standard Step 1 starts.
- Do not rename the standard flow as a "human flow". Human visibility is an experience requirement on top of the standard flow, not a different lifecycle.

## Boundaries

- Do not start V0.3 implementation before the V0.3 change package, requirements, and contract are explicit.
- Do not archive the V0.3 change before independent review passes.
- Do not let the executor approve final review.
- Keep CLI as Agent-internal machinery; human-facing output should be summaries, decisions, owner, blocker, next action, and evidence.
- Do not treat `change prepare` as completion of Step 1-5. It can prepare artifacts, but the standard 9-step flow still starts at Step 1.

## Next Working Move

Create the V0.3 preparation package around:

**Human Participation and Closeout Readability**

The implementation should be sliced so each slice can be dogfooded independently and verified with regression tests plus a full smoke test.
