# Agent-first open-cowork project

本项目已经启用 open-cowork。请把 open-cowork 当成由 Agent 操作的协同治理协议，而不是要求人手动执行的 CLI-first 流程。

## 优先读取

1. `.governance/agent-entry.md`：任意 Agent 接手项目时的固定入口。
2. `.governance/agent-playbook.md`：Agent 操作规则。
3. `.governance/current-state.md`：当前可读状态摘要。
4. `.governance/state.yaml`：v0.3.11 lean compact 权威状态。
5. `.governance/evidence.yaml`、`.governance/ledger.yaml`、`.governance/rules.yaml`：证据引用、接续记录和规则。

只读取当前 active working set。不要默认全文扫描冷历史、历史计划、旧 heavy layout、session JSONL 或大日志；历史文档只在明确需要追溯 source docs 时按路径读取。大型输出必须写入文件并在对话中只引用 evidence ref、路径和短摘要。

## 操作规则

Deterministic protocol trigger: run the project resume / status entry before continuing project work. Natural language is only a request to run the entry, not the protocol trigger.
Do not ask the human to memorize ocw commands. Use `ocw` only as an internal tool when it helps maintain structured facts, evidence, review, closeout, and continuity.

## 硬边界

- 未经人明确同意，不要在 active scope 之外执行。
- 不要让 executor 自己批准最终 review。
- review 通过前不要 closeout。
- 不要在执行过程中暗中改写 scope、role bindings 或 rules。
