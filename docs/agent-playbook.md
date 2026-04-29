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
3. v0.3.11 默认使用 lean protocol；优先读取 `.governance/agent-entry.md` 给出的 bounded read set。
4. 默认权威状态是 `state.yaml`；`current-state.md` 是给人和新 Agent 快速理解的可再生摘要。
5. Step 6 前确认 intent、scope、风险、验收标准、role bindings、Step 5 approval 和 readiness。
6. 关键步骤用状态摘要向人汇报 owner、输入、输出、完成标准、下一步门槛和需要决策的事项。
7. 如果人确认了非阻塞 step，例如 Step 4 任务拆解，记录 acknowledgement，不要把它挪成 Step 5 approval。
8. 进入 Step 6 前确认 Step 5 human gate approval 已记录；不要把 human gate 当成仅展示字段。
9. Step 8 先记录独立 reviewer decision，再让人决定接受、修订或拒绝；不要要求人先批准才能写入 review 结论。
10. 连续迭代时读取 compact baseline，区分 parent closeout dirty baseline、本轮 evidence delta 和无关工作区噪声。
11. 保持 `current-state.md` 对下一个 Agent 可读；closeout 后确认它已经反映已收束或下一步状态。
12. evidence 要客观、有界、可追溯；review 要尽量独立。
13. 只有目标、边界、风险、取舍或批准需要判断时，才让人介入。
14. 用 hygiene / doctor 区分冷历史、pending docs、状态一致性和建议提交内容。

## 交接规则

当另一个 Agent 接手时，先指向：

```text
.governance/AGENTS.md
.governance/agent-entry.md
.governance/current-state.md
.governance/state.yaml
```

然后从当前 round 的 scope、role bindings、rules 和 evidence refs 继续。

不要默认全文读取冷历史。只有接手资料索引、恢复包或人明确指定某个 source doc 时，才按路径读取对应历史文件。
