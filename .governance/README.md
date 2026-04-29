# .governance

本目录是 open-cowork 的项目事实层。v0.3.11 默认采用 lean protocol：当前事实应优先落在少量可读、可验证、可轮转的文件中。

## 当前默认入口

- `AGENTS.md`：项目内 Agent 规则入口。
- `agent-entry.md`：任意 Agent 接手、验证、审查或实现时的固定入口。
- `agent-playbook.md`：本项目 Agent 操作规则。
- `current-state.md`：给人和新 Agent 读取的当前状态摘要。
- `state.yaml`：compact 权威状态，缺失时应先走迁移 / 初始化流程。
- `evidence.yaml`：有界证据引用。
- `ledger.yaml`：closeout、迁移 receipt 和接续记录。
- `rules.yaml`：项目规则与 gate 策略。

旧版本项目可能保留 heavy layout。它们是迁移来源或冷历史，不是 v0.3.11 新项目默认模型。Agent 不应默认全文读取冷历史；只有当前 state、恢复包或人明确指定路径时才按需读取。
