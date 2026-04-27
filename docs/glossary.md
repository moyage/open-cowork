# open-cowork 术语表

本页给人和 Agent 对齐基础概念。术语可以出现在英文文件名或 YAML 字段里，但实践时应优先用这里的中文解释理解。

| 术语 | 简明解释 |
| --- | --- |
| 变更包 / Change package | 一个具体需求或任务的工作单元。它把 intent、requirements、design、tasks、Contract、Bindings、Evidence、Verify、Review 和 Archive 放在同一个目录下。 |
| Contract | 执行契约。说明目标、允许范围、禁止范围、允许动作、禁止动作、验证对象和证据要求。Agent 执行时不能越过它。 |
| Evidence | 执行证据。包括命令输出、测试输出、文件变更摘要、产物路径和执行说明。它用来证明“做过什么”，而不是只靠聊天描述。 |
| Bindings | 角色绑定。说明 sponsor、orchestrator、executor、verifier、reviewer、maintainer 以及每个 Step 的 owner / reviewer / human gate。 |
| Continuity | 接续能力。用于 session 压缩、新会话、换 Agent、owner transfer、下一轮 increment、closeout、sync 和 digest。 |
| Gate | 门。某一步继续前必须满足的条件，常见是 human approval、review required 或 verification pass。 |
| 治理门 / Governance gate | 影响项目是否能继续推进的关键门，例如 Step 5 批准开工、Step 8 独立审查、Step 9 批准归档。 |
| Closeout | 收束说明。记录本轮交付了什么、没交付什么、风险和下一轮建议。 |
| Increment | 增量接续。当前轮次中出现新发现、新风险或新范围时，生成给下一轮或并行工作的结构化输入。 |
| Digest | 压缩摘要。给人或新 Agent 快速读取的状态摘要，避免从长聊天或大量文件里重新考古。 |
| Archive | 归档。把完成的 change package 变成可追溯历史事实，并刷新项目维护状态。 |
| Current state | 当前状态快照。目标项目 `.governance/local/current-state.md`，新会话和另一个 Agent 优先读取。 |
| Approval token | 可选的人持有令牌。用于把 Step approval 从“文本声明”提升为本地可信确认。 |
| Review decision | 独立审查结论。只表示 reviewer 的 approve / revise / reject，不等同于人批准进入 review。 |
| Project activation | 项目级激活。任意 Agent 在已实施 open-cowork 的项目中读取 `.governance` 当前事实，并接续 active change。 |
