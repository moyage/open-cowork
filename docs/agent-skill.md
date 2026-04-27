# open-cowork Agent Entry 与平台 Skill

本页说明目标项目中的 `.governance/agent-entry.md`。它放在 `.governance/` 下，是因为它属于项目级协作事实和接手规则，需要跟项目一起走；它不是某个 Agent 平台专属的安装型 Skill，也不是给人背诵的命令手册。

如果 Agent 环境支持自定义 Skill，可以把 `.governance/agent-entry.md` 的内容注册进去；如果不支持，Agent 直接把它当成项目内接手说明读取即可。换句话说：

- `.governance/agent-entry.md` 是项目权威入口。
- 平台 Skill 是可选适配层。
- 不同 Agent 平台的适配文件不应该取代项目事实层。

## 触发场景

当人对 Codex、Claude Code、Hermes、OMOC、OpenClaw 或其他 Agent 说：

```text
请用 open-cowork 继续这个项目。
```

或：

```text
请接续需求 1 / 需求 2 的 open-cowork 进展。
```

或：

```text
这个项目已经实施 open-cowork，请按项目里的 open-cowork 接手规则接续当前需求。
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
