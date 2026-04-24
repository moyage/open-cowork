# Changelog

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
