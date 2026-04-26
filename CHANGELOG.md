# Changelog

## 0.3.0

- Promoted the standard 9-step runtime flow into human-visible Step 1-9 reports, while keeping the 4 traditional human phases as explanatory mapping only
- Separated `change prepare` from Step 1-5 completion so preparation cannot imply hidden human approval or skipped steps
- Added `gate_type`, `gate_state`, and `approval_state` across status snapshots and step progress, removing misleading approval-pending semantics from review-only steps
- Added human-facing step reports with `framework_controls`, `agent_actions_done`, `agent_actions_expected`, clear inputs/outputs, done criteria, next-entry criteria, and short approve/revise/reject confirmation options
- Strengthened Step 5, Step 8, and Step 9 human-gate traceability, including Step 8 review approval references and final Step 5/8/9 gate summaries in archive consistency checks
- Hardened reviewer mismatch bypass auditing with required human-readable reason, recorder, and evidence reference
- Updated Agent-first adoption, onboarding, current-state, and playbook docs for human-visible participation and closeout readability
- Added V0.3 regression coverage for prepare-state semantics, human-gate reports, status approval semantics, review/archive traceability, and idle current-state consistency

## 0.2.9

- Enforced Step 8 human approval before `ocw review` and Step 9 human approval before `ocw archive`
- Turned reviewer mismatch from a warning into a blocking review error unless an explicit audited bypass is requested
- Added approval provenance fields for `recorded_by` and `evidence_ref`
- Finalized archive traceability by recording the archived Step 9 report in `archive-receipt.yaml`
- Expanded human-readable `ocw step report` text output with inputs, outputs, done criteria, and participant responsibilities
- Added a 9-step `ocw status` progress table with approval state for human-gated steps
- Updated smoke and regression coverage for v0.2.9 review/archive gate closure
- Updated Agent-first docs for the v0.2.9 release and next external dogfood round

## 0.2.8

- Added explicit step participant mapping for `ocw participants setup` with `--step-owner`, `--step-assistant`, and `--step-reviewer`
- Preserved existing participant bindings when `ocw change prepare` is rerun after participant setup
- Added `ocw step approve` and Step 5 human-gate enforcement before `ocw run`
- Generated default Step 1-9 reports through intent, prepare, run, verify, review, and archive flows
- Added human-readable recovery for draft-contract `ocw step report` calls
- Added intent/contract scope drift detection during `ocw contract validate`
- Added reviewer mismatch warnings and final archive state consistency snapshots
- Updated adoption, bootstrap, quickstart, and smoke-test guidance for the v0.2.8 enforceable human-gates flow

## 0.2.7

- Added `ocw participants setup` to create a personal-domain participant profile and 9-step owner / assistant / reviewer / human-gate matrix
- Added `ocw intent capture` and `ocw intent confirm` to make requirements, optimizations, bugs, scope, risks, acceptance criteria, and human confirmation visible before execution
- Added `ocw step report` to materialize human-readable step reports with owner, inputs, outputs, done criteria, next-entry criteria, blockers, and human decisions
- Added archive-time `.governance/current-state.md` synchronization and `ocw status --sync-current-state`
- Extended `ocw hygiene` / `ocw doctor` with human-readable and machine-readable state consistency diagnostics
- Updated bootstrap, quickstart, and smoke-test release checks for the v0.2.7 human-control flow

## 0.2.6

- Added `ocw adopt --dry-run` for Agent-first adoption planning from natural-language goals, source docs, and personal-domain agent inventory
- Added `--source-doc` support to `ocw change prepare` and records source documents in generated intent, requirements, and manifest files
- Aligned `ocw run` write boundaries with contract `scope_in/scope_out` and added scope conflict validation
- Added bounded recommended read sets to Agent handoff outputs to avoid archive-history context explosions
- Added `ocw hygiene` / `ocw doctor` to classify runtime artifacts, Agent handoff files, pending docs, tracked truth sources, and ignored governance artifacts
- Added support for manual analysis/report evidence refs as first-class evidence inputs when explicitly scoped by contract
- Updated onboard/pilot defaults so Agents start from adoption planning and `current-iteration` instead of a fixed `personal-demo` path
- Updated bootstrap, quickstart, and smoke-test release checks to validate `ocw version`, adoption planning, and hygiene diagnostics

## 0.2.5

- Added repository-level `AGENTS.md` as the Agent-first adoption entry
- Added `docs/agent-adoption.md` and `docs/agent-playbook.md` for natural-language adoption and Agent operation rules
- Generated target-project `.governance/AGENTS.md`, `.governance/agent-playbook.md`, and `.governance/current-state.md` from `change prepare` and `pilot`
- Reframed README and getting-started docs around Agent-first usage instead of CLI-first operation
- Updated pilot and change prepare output to point Agents at handoff files instead of asking humans to copy long command prompts

## 0.2.4

- Added `ocw version` / `open-cowork version` for upgrade diagnostics
- Added `scripts/update.sh` and `scripts/bootstrap.sh --clean` for smooth V0.2.3 -> V0.2.4 upgrades
- Added `ocw change prepare` to fill intent, requirements, design, tasks, contract, and bindings for a change package
- Added `ocw pilot` as a one-command personal-domain pilot setup path
- Updated README and getting-started docs with upgrade, reinstall, guided pilot, and agent prompt instructions

## 0.2.3

- Added `ocw onboard` and `ocw setup` for interactive or scripted project onboarding
- Added `open-cowork` console script alias for clearer first-use commands
- Updated bootstrap shim fallback to expose both `ocw` and `open-cowork` commands
- Reworked `scripts/quickstart.sh` to call the onboarding flow after bootstrap
- Updated README and getting-started docs for onboarding/setup usage

## 0.2.2

- Expanded `README.md` with positioning, background, goals, scenarios, 4-phase/9-step flow, roadmap, feature status, and document index
- Added `scripts/quickstart.sh` for one-command install plus target-project initialization
- Updated `docs/getting-started.md` to prefer the quickstart path while preserving manual setup

## 0.2.1

- Consolidated onboarding docs into `docs/getting-started.md`
- Moved historical plans and reports into `docs/archive/`
- Rewrote `docs/README.md` as a concise document map
- Localized governance and community docs into Chinese
- Clarified `.governance/` as runtime artifact storage instead of a documentation area

## 0.2.0

- Landed the Milestone 1 complex collaboration runtime chain
- Added verify/review/archive gates and minimum state transition protection
- Added runtime status and timeline machine-readable outputs
- Added continuity primitives: handoff, owner transfer, increment, closeout, sync, history, export, and digest
- Hardened governance reserved boundaries and archive/maintenance consistency checks
- Added grouped sync summaries and digest reading compression for human/team use
- Added bootstrap and smoke-test scripts for first-time team adoption
- Added personal-domain multi-agent pilot guidance and role-mapping samples
- Made draft change `status` and `continuity digest` outputs friendly before contract completion
- Updated onboarding docs for the current CLI and v0.2 readiness

## 0.1.0

- Repository cleanup for public sharing
- Runtime residue removed from tracked baseline
- Added packaging (`pyproject.toml`) and installable `ocw` entrypoint
- Added open-source onboarding docs (`README`, `docs/getting-started.md`, `CONTRIBUTING`)
- Added session diagnosis/recovery command names (`diagnose-session`, `session-recovery-packet`)
- Hardened tests to use self-contained fixtures instead of repo-bound historical data
