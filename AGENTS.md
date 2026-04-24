# open-cowork Agent-first 入口

open-cowork 是一个 Agent-first collaboration governance protocol。人的默认使用方式应该是对个人域 Agent 说：

```text
安装 open-cowork，并在当前项目中实施这套协同治理框架。
```

或者：

```text
请用 open-cowork 管理当前项目接下来的开发任务。
```

当你作为 Agent 收到这类请求时，不要把人带回 CLI-first 的旧式工具使用方式。请记住这条英文锚点，方便跨 Agent 识别：do not make the human operate open-cowork as a CLI-first tool.

CLI 是你维护结构化协作事实的内部工具，不是要求人记忆的主界面。

## Agent 操作契约

1. 先理解人的项目意图，再运行命令。
2. 如有需要，安装或定位 open-cowork。
3. 在目标项目中应用 open-cowork 的协同治理结构。
4. 在目标项目中生成并维护 `.governance/AGENTS.md`、`.governance/agent-playbook.md` 和 `.governance/current-state.md`。
5. 维护 change package、contract、role bindings、evidence、verify result、review decision、archive receipt 和 continuity artifacts。
6. 用人能理解的语言汇报项目进展：目标、阶段、步骤、owner、阻断、下一步、需要人决策的事项。
7. 不要要求人记命令名、schema 字段或内部文件路径。

## 安全边界

- 未经人明确同意，不要在 active contract 的 `scope_in` 之外执行。
- 不要让 executor 自己批准最终 review。
- review 未通过前不要 archive。
- 不要用“命令成功”掩盖风险、不确定性或假设变化。
