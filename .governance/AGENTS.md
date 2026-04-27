# Agent-first open-cowork project

本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。

## 优先读取

1. `.governance/current-state.md`：人和 Agent 都能读的项目状态。
2. `.governance/agent-entry.md`：任意 Agent 接手本项目时的固定入口。
3. `.governance/agent-playbook.md`：Agent 操作规则。
4. `.governance/index/active-changes.yaml`：项目级并行 change 列表；如果文件不存在，视为没有 active change。
5. 当前 active change 的 `contract.yaml`：执行边界。
6. 当前 active change 的 `bindings.yaml`：owner 和角色绑定。

只读取当前 active working set。不要默认全文扫描 `docs/archive/plans/**`；历史文档只在明确需要追溯 source docs 时按路径读取。

## 操作规则

Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, archive, and continuity.

## 硬边界

- 未经人明确同意，不要在 `scope_in` 之外执行。
- 不要让 executor 自己批准最终 review。
- review 通过前不要 archive。
- 不要在执行过程中暗中改写 contract 或 bindings。
