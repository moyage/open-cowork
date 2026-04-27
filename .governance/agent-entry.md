# open-cowork Agent Entry

Use this project entry whenever a human asks any local Agent to continue, review, verify, or implement work in this project.

This file is the project-scoped source of truth for Agent handoff. It can be registered as a platform Skill when supported, but it is not tied to any single Agent runtime.

## Deterministic protocol trigger

- Reliable trigger: run `ocw resume` in the project root.
- List work: run `ocw resume --list`.
- Continue explicit work: run `ocw resume --change-id <change-id>`.
- Natural-language phrasing is only a request to run this command; do not rely on keywords, language, or chat history.
- `.governance/local/**` is a local projection, not team-authoritative truth.

## Activation rule

1. Treat open-cowork as project-scoped, not Agent-scoped.
2. Run deterministic project resume internally before acting.
3. If multiple active changes exist, select the explicit change requested by the human; otherwise ask for the change_id before execution.
4. Read only the recommended read set from resume.
5. Never reconstruct project state from chat history when `.governance/` facts exist.

## Default internal activation

- Use `ocw resume` to discover whether the project has one active change, multiple active changes, or no active change.
- Use `ocw resume --change-id <change-id>` when the human has selected a specific work item.

## Human-facing report

Report in this shape, without exposing command lists:

```text
当前项目推进状态

- 项目目标：
- 当前 change：
- 当前步骤：
- 当前 Owner：
- 已完成：
- 当前阻断：
- 下一步建议：
- 需要你决策：
- Agent 后续动作：
```

## Hard boundaries

- Do not execute outside the active contract scope.
- Do not let the executor approve its own final review.
- Do not archive before review approval and Step 9 human approval.
- Do not ask the human to memorize open-cowork CLI commands.
