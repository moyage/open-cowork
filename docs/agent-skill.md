# open-cowork Agent Skill

本页说明目标项目中的 `.governance/open-cowork-skill.md`。它不是给人背诵的命令手册，而是给任意本地个人域 Agent 的固定接手规则。

## 触发场景

当人对 Codex、Claude Code、Hermes、OMOC、OpenClaw 或其他 Agent 说：

```text
请用 open-cowork 继续这个项目。
```

或：

```text
请接续需求 1 / 需求 2 的 open-cowork 进展。
```

Agent 必须把 open-cowork 当成项目级框架，而不是当前会话私有状态。

## Agent 必须做什么

1. 先做项目级 activation。
2. 如果项目里有多个 active changes，先确认或选择 change_id。
3. 只读取 activation 给出的 recommended read set。
4. 以 active change 的 contract 作为执行边界。
5. 以 bindings 作为 owner、reviewer 和 human gate 映射。
6. 用人能理解的状态面汇报，不展示命令清单。
7. 执行、验证、审查和归档都必须写回 `.governance/`。

## 人应该看到什么

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

## 关键边界

- open-cowork 的应用对象是项目，不是 Agent。
- 不要让人记 open-cowork CLI。
- 不要从聊天历史重建状态。
- 不要默认全文扫描 archive。
- 不要让 executor 自己批准最终 review。
