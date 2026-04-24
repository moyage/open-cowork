# Agent-first open-cowork project

本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。

## 优先读取

1. `.governance/current-state.md`：人和 Agent 都能读的项目状态。
2. `.governance/agent-playbook.md`：Agent 操作规则。
3. `.governance/index/current-change.yaml`：当前 active change 指针。
4. `.governance/index/maintenance-status.yaml`：最近归档与维护状态。

如果当前状态是 `idle`，不要读取旧 active change 的完整运行态包。需要追溯时，优先读取 `.governance/archive/<change-id>/archive-receipt.yaml` 和对应 review/manifest。

## 操作规则

Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, archive, and continuity.

## 硬边界

- 未经人明确同意，不要在 `scope_in` 之外执行。
- 不要让 executor 自己批准最终 review。
- review 通过前不要 archive。
- 不要在执行过程中暗中改写 contract 或 bindings。
