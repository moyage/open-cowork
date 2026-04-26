# Agent-first open-cowork project

本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。

## 优先读取

1. `.governance/current-state.md`：人和 Agent 都能读的项目状态。
2. `.governance/agent-playbook.md`：Agent 操作规则。
3. `.governance/index/maintenance-status.yaml`：最近归档与维护状态。
4. `docs/archive/reports/2026-04-26-v030-release-and-next-dogfood.md`：最近一次正式发布说明。
5. `.governance/archive/v0.3-human-participation-closeout-readability/archive-receipt.yaml`：最近归档收据。

当前没有 active change。只读取当前 idle / release working set。不要默认全文扫描 `docs/archive/plans/**`；历史文档只在明确需要追溯 source docs 时按路径读取。

## 操作规则

Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, archive, and continuity.

## 硬边界

- 未经人明确同意，不要在 `scope_in` 之外执行。
- 不要让 executor 自己批准最终 review。
- review 通过前不要 archive。
- 不要在执行过程中暗中改写 contract 或 bindings。
- idle 状态下不要把最近归档包当成 active change；新任务必须新建或明确设置 active change。
