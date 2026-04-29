# v0.3.11 Lean Protocol Reset

## Goal

v0.3.11 resets the open-cowork runtime model so projects can use the framework for dozens or hundreds of rounds, across many days and many Agents, without making the project slower, heavier, or harder to resume.

This is a breaking-level protocol simplification shipped as v0.3.11, not v4.0. The version remains in the v0.3 line because the project is still maturing its public operating model before broad team and open source adoption.

## Non-Negotiable Outcomes

1. A project using open-cowork for 100 rounds must still have a small default Agent read set.
2. Active governance state must stay bounded in file count and size.
3. One round must not create a directory tree of intermediate files when one durable record can carry the same meaning.
4. Personal single-Agent, personal multi-Agent, and team multi-Agent workflows must use the same compact state model.
5. Historical records must be append-only summaries by default, not copied working directories.
6. Large command output, logs, long review transcripts, session dumps, and source documents must be referenced by digest or external path, not embedded into default governance context.
7. Resume must not require scanning cold history.

## Supported Adoption Scenarios

### A. Personal Domain, Single Agent, One Or More Projects

The framework must help one Agent maintain continuity without turning every project into a growing governance archive. The Agent should read the project entry files, the compact state file, and the current round record. Older rounds remain in a compact ledger and are not loaded unless the human asks for historical analysis.

### B. Personal Domain, Multiple Agents, One Or More Projects

The framework must let Codex, Hermes, OMOC/OpenCode, Claude Code, Gemini, or other personal-domain Agents coordinate through the same compact state. Agent participation is recorded as role bindings and decision records inside the current round, not as per-Agent directory sprawl.

### C. Team Domain, Multiple Agents, One Or More Projects

The framework must support many humans and Agents while keeping the project state light. Team coordination uses participants, role bindings, gates, review decisions, and carry-forward records in the compact model. Team size must not multiply the number of generated files per step.

## New Governance Layout

The v0.3.11 default layout is:

```text
.governance/
  AGENTS.md
  agent-entry.md
  agent-playbook.md
  state.yaml
  current-state.md
  ledger.yaml
  evidence.yaml
  templates/
```

Optional cold storage may exist, but must never be part of the default read set:

```text
.governance/cold/
  legacy/
  artifacts/
```

Deprecated by default:

```text
.governance/changes/
.governance/archive/
.governance/runtime/
.governance/index/
.governance/local/
```

These legacy directories may be migrated or kept as cold history, but v0.3.11 commands must not create them during normal operation.

## File Responsibilities

### `.governance/state.yaml`

The only machine-authoritative current state file.

It contains:

- protocol version
- active round id
- phase
- gate state
- scope
- owners and participants
- current decision needed
- verification status
- review status
- carry-forward summary
- bounded references to evidence

It must not contain full command output, long review transcripts, or copied source documents.

### `.governance/current-state.md`

Human and Agent readable short summary generated from `state.yaml`.

It should remain short enough to read in one screen:

- current goal
- active phase
- owner
- blocked or not
- next decision
- latest verification result
- latest review decision
- carry-forward notes

This file is allowed to duplicate selected state because it serves a different consumer, but it must be generated from `state.yaml` and remain bounded.

### `.governance/ledger.yaml`

Append-only compact round ledger.

Each round record contains:

- round id
- dates
- goal
- scope digest
- participants
- final status
- verification summary
- review summary
- evidence refs
- closeout summary
- next carry-forward item

The ledger is the historical source of truth. It does not store full working files for each round.

### `.governance/evidence.yaml`

Bounded evidence index.

Each evidence item contains:

- evidence id
- round id
- kind
- path or external ref
- short summary
- optional hash
- created by
- created at

Large artifacts stay where they naturally belong: build logs, CI output, screenshots, test reports, local session recovery files, or external systems. open-cowork records references and summaries.

## Round Model

v0.3.11 replaces the file-heavy change package with one compact round object.

Required fields:

```yaml
round_id: R-20260429-001
goal: "Short user-facing goal"
phase: plan|execute|verify|review|closed
scope:
  in: []
  out: []
participants:
  sponsor: human
  orchestrator: agent
  executor: agent
  reviewer: agent-or-human
gates:
  execution: pending|approved|blocked
  closeout: pending|approved|blocked
evidence_refs: []
verify:
  status: not-run|pass|fail|blocked
  summary: ""
review:
  status: not-requested|approve|revise|reject
  reviewer: ""
closeout:
  status: open|closed
  summary: ""
carry_forward: []
```

The CLI may serialize this inside `state.yaml` for the active round and append a compact copy into `ledger.yaml` when the round closes.

## Flow Simplification

The previous nine-step flow is replaced by five phases:

1. **Intent and Scope**
   Capture the human goal, scope in/out, known constraints, and success criteria.

2. **Plan and Contract**
   Produce a compact executable plan and confirm who may execute, what may be changed, and how completion will be verified.

3. **Execute and Evidence**
   Perform the work and record bounded evidence refs. Do not embed long logs or transcripts.

4. **Verify and Review**
   Run verification, summarize results, and record an independent review decision when required.

5. **Closeout and Carry-Forward**
   Close the round, append one compact ledger entry, update current state, and record next actions.

Human gates remain mandatory before execution and closeout when policy requires them, but each gate is recorded inside the active round object instead of generating separate step files.

## Default Read Set

An Agent entering an implemented project reads only:

```text
.governance/AGENTS.md
.governance/agent-entry.md
.governance/current-state.md
.governance/state.yaml
```

Optional reads:

```text
.governance/ledger.yaml
.governance/evidence.yaml
```

Cold history is never read by default.

## Context Budget Rules

1. `current-state.md` should target less than 200 lines.
2. `state.yaml` should target less than 400 lines.
3. `ledger.yaml` should keep compact round records and support pruning or rotation when it grows.
4. `evidence.yaml` should record summaries and refs only.
5. Commands that can emit large output must write artifacts outside the default read set and register a short evidence ref.
6. Resume, status, preflight, and review entry commands must not scan cold history.

## Cold History And Migration

Existing projects may already contain:

- `.governance/changes/**`
- `.governance/archive/**`
- `.governance/runtime/**`
- `.governance/index/**`
- `.governance/local/**`

v0.3.11 migration should:

1. Read the current active state if available.
2. Create `state.yaml`, `current-state.md`, `ledger.yaml`, and `evidence.yaml`.
3. Convert archived change receipts into compact ledger records.
4. Convert active change manifest, contract, verify, review, and archive receipt into a current round when possible.
5. Move or mark legacy directories as cold history.
6. Update `.gitignore` so cold/runtime/cache paths do not become normal source context.

Migration must preserve auditability by refs and summaries, but it must not copy full old trees into the new active model.

## Command Direction

The CLI should remain Agent-internal. Humans should not be asked to operate it as the main interface.

Recommended command model:

- `ocw init`: create the compact layout.
- `ocw resume`: read the compact default read set only.
- `ocw round start`: create or replace the active round in `state.yaml`.
- `ocw round approve`: record human or policy gate approval in `state.yaml`.
- `ocw evidence add`: append a bounded evidence ref to `evidence.yaml`.
- `ocw verify`: update compact verify summary.
- `ocw review`: update compact review decision.
- `ocw round close`: append one compact ledger record and reset active state.
- `ocw migrate lean`: convert legacy governance trees into v0.3.11 compact state.
- `ocw hygiene`: report file counts, sizes, default read set size, cold history, and cleanup candidates.

Legacy commands may remain as compatibility shims for one release, but normal docs and generated Agent entry files must point to the lean commands.

## Testing Strategy

v0.3.11 requires tests that protect against future bloat.

### Unit Tests

- `init` creates only the compact default layout.
- starting a round updates only `state.yaml` and `current-state.md`.
- adding evidence appends bounded refs without embedding long output.
- closing a round appends one compact ledger record.
- resume uses the compact default read set.
- migration converts representative legacy projects without losing key summaries.

### Long-Run Pressure Tests

Simulate:

- 100 rounds in one project with one Agent.
- 100 rounds in one project with several Agents.
- multiple projects each with repeated rounds.
- team-style participants and independent reviewers.

Assertions:

- default read set file count remains fixed.
- default read set total size remains bounded.
- per-round generated file count remains near constant.
- no command scans cold history during resume/status/preflight.
- archive/ledger growth is compact and rotatable.

### Regression Guards

Add tests that fail if normal round execution creates legacy directories:

```text
.governance/changes/
.governance/archive/
.governance/runtime/
.governance/index/
.governance/local/
```

Compatibility migration tests may create those directories intentionally.

## Documentation Updates

Update:

- `README.md`
- `docs/getting-started.md`
- `docs/agent-adoption.md`
- `docs/agent-playbook.md`
- `docs/glossary.md`
- `.governance/AGENTS.md`
- `.governance/agent-entry.md`
- `.governance/agent-playbook.md`

The docs must explain that open-cowork is Agent-first and compact by default. They must stop presenting `.governance/changes/**` and `.governance/archive/**` as the normal operating model.

## Release Acceptance Criteria

v0.3.11 is ready when:

1. New projects initialize with the lean layout.
2. Resume reads only the compact default read set.
3. A full round can start, execute, verify, review, and close without creating legacy runtime trees.
4. Legacy migration produces compact state and ledger records.
5. Long-run pressure tests pass.
6. Existing v0.3.10 projects have a clear migration path.
7. Documentation describes the lean protocol as the default.
8. The open-cowork repository itself is migrated to the lean self-dogfood layout before release.

## Implementation Decisions

These decisions are fixed for v0.3.11 implementation:

1. `ledger.yaml` remains the default ledger file. `ocw hygiene` warns when it exceeds 500 compact round records or 512 KB. Automatic rotation is allowed only through an explicit `ocw hygiene --rotate-ledger` action so Agents do not surprise users during normal work.
2. `evidence.yaml` remains the default evidence index. `ocw hygiene` warns when it exceeds 1,000 refs or 512 KB. Large evidence is always stored out of the default read set and referenced by summary.
3. Normal v0.3.11 commands must not create legacy directories. Compatibility shims may read legacy directories for migration and may warn when old commands are used.
4. Legacy command names may remain as aliases for one release when they can map cleanly to the new round model. If a legacy command would require creating `changes/`, `archive/`, `runtime/`, `index/`, or `local/`, it must fail with migration guidance instead of silently recreating the old model.
5. `current-state.md` is regenerated from `state.yaml`; manual edits to it are not authoritative.
6. The open-cowork repository must dogfood the lean layout before tagging v0.3.11.
