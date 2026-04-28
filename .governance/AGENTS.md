# Agent-first open-cowork project

本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。

## 优先读取

1. `.governance/agent-entry.md`：任意 Agent 接手项目时的固定入口。
2. `.governance/agent-playbook.md`：Agent 操作规则。
3. `.governance/index/active-changes.yaml`：项目级并行 change 列表。
4. `.governance/local/current-state.md`：本地可再生状态投影。
5. `ocw resume` 输出的 recommended read set：当前 change 的权威事实。

只读取当前 active working set。不要默认全文扫描 `docs/archive/plans/**`；历史文档只在明确需要追溯 source docs 时按路径读取。

## 操作规则

Deterministic protocol trigger: run `ocw resume` before continuing project work. Natural language is only a request to run the command, not the protocol trigger.
Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, archive, and continuity.
Before modifying project files, run execution preflight through open-cowork. If preflight says project files cannot be modified, stop and report the missing active change, gate, contract, scope, or readiness item. Do not complete implementation first and then ask whether to backfill open-cowork.

## 硬边界

- 未经人明确同意，不要在 `scope_in` 之外执行。
- 未经人明确同意，不要缩减需求、`scope_in`、验收标准或任务完成定义。
- 不要让 executor 自己批准最终 review。
- review 通过前不要 archive。
- 不要在执行过程中暗中改写 contract 或 bindings。
- 不要把完整需求自行降级为最小实现、部分实现或后续再补。
- 不要把事后补录伪装成正常 Step 6 evidence；绕过流程只能记录为 recovery。
