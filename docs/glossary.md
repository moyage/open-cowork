# open-cowork 术语表

本页给人和 Agent 对齐基础概念。术语可以出现在英文文件名或 YAML 字段里，但实践时应优先用这里的中文解释理解。

| 术语 | 简明解释 |
| --- | --- |
| Round / 工作轮次 | 一个具体需求或任务的轻量工作单元。它把目标、范围、角色、证据引用、验证、审查和接续记录聚合在 compact state 中。 |
| Scope | 执行范围。说明目标、允许范围、禁止范围、允许动作、禁止动作、验证对象和证据要求。Agent 执行时不能越过它。 |
| Contract | 旧版“变更包 / contract”模型中的执行契约。v0.3.11 新项目默认使用 round scope，但旧 contract 仍作为迁移、审查和兼容读取语义保留。 |
| 变更包 | 旧版 change package。用于把需求、契约、证据和审查材料聚合在一起；lean protocol 中对应当前 round、scope、evidence refs 和 ledger。 |
| Evidence refs | 执行证据引用。包括命令输出、测试输出、文件变更摘要、产物路径和执行说明的有界引用。它用来证明“做过什么”，而不是只靠聊天描述。 |
| Role bindings / Bindings | 角色绑定。说明 sponsor、orchestrator、executor、verifier、reviewer、maintainer 以及每个 Step 的 owner / reviewer / human gate。 |
| Continuity | 接续能力。用于 session 压缩、新会话、换 Agent、owner transfer、下一轮 increment、closeout、sync 和 digest。 |
| Gate | 门。某一步继续前必须满足的条件，常见是 human approval、review required 或 verification pass。 |
| 治理门 / Governance gate | 影响项目是否能继续推进的关键门，例如 Step 5 批准开工、Step 8 独立审查、Step 9 批准收束。 |
| Closeout | 收束说明。记录本轮交付了什么、没交付什么、风险和下一轮建议。 |
| Increment | 增量接续。当前轮次中出现新发现、新风险或新范围时，生成给下一轮或并行工作的结构化输入。 |
| Digest | 压缩摘要。给人或新 Agent 快速读取的状态摘要，避免从长聊天或大量文件里重新考古。 |
| Ledger | 接续账本。记录 closeout、carry-forward、迁移 receipt 和重要 lifecycle 事件。 |
| Current state | 当前状态快照。目标项目 `.governance/current-state.md`，新会话和另一个 Agent 优先读取。 |
| Approval token | 可选的人持有令牌。用于把 Step approval 从“文本声明”提升为本地可信确认。 |
| Review decision | 独立审查结论。只表示 reviewer 的 approve / revise / reject，不等同于人批准进入 review。 |
| Project activation | 项目级激活。任意 Agent 在已实施 open-cowork 的项目中读取当前项目事实，并接续 active round。 |
| Cold history | 从旧版本 heavy layout 迁移出来的历史材料。它用于追溯，不进入默认读取集。 |
