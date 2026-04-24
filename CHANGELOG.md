# Changelog

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
