# open-cowork Agent Entry

Use this project entry whenever a human asks any local Agent to continue, review, verify, or implement work in this project.

This file is the project-scoped source of truth for Agent handoff. It can be registered as a platform Skill when supported, but it is not tied to any single Agent runtime.

## Deterministic protocol trigger

- Reliable trigger: run the project resume / status entry in the project root.
- Natural-language phrasing is only a request to run that entry; do not rely on keywords, language, or chat history.
- v0.3.11 default model is lean protocol: read the small current working set first, not cold history.

## Recommended read set

1. `.governance/AGENTS.md`
2. `.governance/agent-playbook.md`
3. `.governance/current-state.md`
4. `.governance/state.yaml`
5. `.governance/evidence.yaml`
6. `.governance/ledger.yaml`
7. `.governance/rules.yaml`

If a file is missing during migration, report the missing fact explicitly and use the migration / verify flow before execution.

## Context discipline

- Do not full-scan cold history, archives, session JSONL, or large logs unless `state.yaml`, `current-state.md`, or a recovery handoff points to a specific path.
- Write large command output, reviews, and recovery data to files; cite evidence refs and short summaries in chat.
- Use targeted reads with line ranges, filters, or summaries. Keep `current-state.md` under 200 lines and `state.yaml` under 400 lines.
- After compact failure, resume from the generated handoff and last successful evidence instead of rereading the failed transcript.

## Activation rule

1. Treat open-cowork as project-scoped, not Agent-scoped.
2. Run deterministic project resume / status internally before acting.
3. If exactly one active round exists, continue that round after reporting its scope and readiness.
4. If multiple active rounds exist and the human named one, select that explicit target; if multiple exist and no target was named, ask which round to continue before execution.
5. Read only the recommended read set unless a state entry points to a specific evidence or cold-history path.
6. Never reconstruct project state from chat history when `.governance/` facts exist.

## Human-facing report

Report in this shape, without exposing command lists:

```text
当前项目推进状态

- 项目目标：
- 当前 round：
- 当前步骤：
- 当前 Owner：
- 已完成：
- 当前阻断：
- 下一步建议：
- 需要你决策：
- Agent 后续动作：
```

## Hard boundaries

- Do not execute outside the active scope.
- Do not let the executor approve its own final review.
- Do not close out before review approval and Step 9 human approval.
- Do not ask the human to memorize open-cowork CLI commands.
