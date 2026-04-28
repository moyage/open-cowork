# 00. Overview

open-cowork 是一个 Agent-first collaboration governance protocol。它的作用对象是项目，而不是单个 Agent、单个会话或某个 IDE。

## 目标

- 让复杂任务从聊天意图进入项目级结构化事实。
- 让多个 Agent 能围绕同一个 active change 接续工作。
- 让 scope、owner、evidence、review、archive 和 continuity 可审计。
- 让人用自然语言发起和决策，而不是背 CLI 命令。
- 让已确认需求按完整范围推进；任何降级、拆分或延期都必须先获得人的明确批准并记录为事实。

## 非目标

- 不替代 IDE、AI Coding runtime、issue tracker 或 CI。
- 不要求所有成员使用同一种 Agent。
- 不把历史计划和过程报告作为当前实施入口。
- 不让 executor 自己批准最终 review。
- 不允许 Agent 未经批准把完整需求自行改写为最小实现、部分实现或后续再补。

## 完整实现原则

所有进入 change package 的需求、`scope_in`、验收标准和任务完成定义，默认都要求完整实现。若 Agent 发现范围过大、风险过高、依赖缺失或需要拆分，必须停在当前步骤提出范围修订、拆分方案或阻断说明，并在 change package 中留下记录。只有在人明确批准后，才能调整范围、降级验收或把内容移入后续迭代。

未经批准的降级不得作为 Step 6 完成、Step 7 验证通过、Step 8 review approve 或 Step 9 archive 的依据。

## 项目事实层

目标项目的 `.governance/` 是运行时事实层。新会话或另一个 Agent 必须先读取：

- `.governance/AGENTS.md`
- `.governance/local/current-state.md`
- `.governance/agent-playbook.md`
- `.governance/changes/<change-id>/contract.yaml`
- `.governance/changes/<change-id>/bindings.yaml`

如果项目已经实施 open-cowork，Agent 应运行 `ocw activate` 读取项目级 activation 状态，不应重新从聊天历史推断。
