# Agent 操作手册

本手册面向 Codex、Claude Code、Cursor、OpenClaw、Hermes、OMOC 或任何被要求采用 / 运行 open-cowork 的本地个人域 Agent。

## 默认汇报格式

当你在一个项目中运行 open-cowork 时，优先用下面结构向人汇报：

```text
当前项目推进状态

- 项目目标：
- 当前阶段：
- 当前步骤：
- 当前 Owner：
- 已完成：
- 当前阻断：
- 下一步建议：
- 需要你决策：
- Agent 后续动作：
```

## 操作规则

1. 先理解自然语言意图，再调用工具。
2. 把 `ocw` 命令当成内部工具，不要当成人的任务清单。
3. 优先生成或读取 adoption plan，确认 source docs、active change 生命周期和推荐 read set。
4. 优先确认 participants profile，让人看到 9 步 owner、assistant、reviewer 和 human gate。
5. 在 Step 6 前确认 intent：需求、优化、Bug、范围、非目标、风险和验收标准。
6. 关键步骤使用 `ocw step report` 生成阶段报告，再向人汇报 owner、输入、输出、完成标准、下一步门槛和需要决策的事项。
7. 保持 `.governance/current-state.md` 对下一个 Agent 可读；archive 后确认它已经回到 idle / archived 状态。
8. evidence 要客观，review 要尽量独立。
9. 只有目标、边界、风险、取舍或批准需要判断时，才让人介入。
10. 用 `ocw hygiene` / `ocw doctor` 区分 runtime generated、pending docs、cold archive docs、状态一致性和建议提交内容。

## 交接规则

当另一个 Agent 接手时，先指向：

```text
.governance/AGENTS.md
.governance/current-state.md
.governance/agent-playbook.md
```

然后从 active change 的 contract 和 bindings 继续。

不要默认全文读取 `docs/archive/**`。只有 adoption plan、handoff package 或人明确指定某个 source doc 时，才按路径读取对应历史文件。
