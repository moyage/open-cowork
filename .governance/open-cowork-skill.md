# open-cowork Project Skill

Use this skill whenever a human asks any local Agent to continue, review, verify, or release work in this repository.

## Activation Rule

1. Treat open-cowork as project-scoped, not Agent-scoped.
2. Run project activation internally before acting when `.governance/index/` is present.
3. If multiple active changes exist, select the explicit change requested by the human before execution.
4. Read only the recommended read set from activation.
5. Never reconstruct project state from chat history when `.governance/` facts exist.

## Human-Facing Report

Report progress without exposing command lists:

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

## Boundaries

- Do not ask the human to memorize open-cowork CLI.
- Do not execute outside the active contract without explicit human approval.
- Do not let executor self-approve final review.
- Do not archive before review evidence and human acceptance are recorded.
