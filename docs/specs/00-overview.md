# 00. Overview

open-cowork 是一个 Agent-first collaboration governance protocol。它的作用对象是项目，而不是单个 Agent、单个会话或某个 IDE。

## 目标

- 让复杂任务从聊天意图进入项目级结构化事实。
- 让多个 Agent 能围绕同一个 active change 接续工作。
- 让 scope、owner、evidence、review、archive 和 continuity 可审计。
- 让人用自然语言发起和决策，而不是背 CLI 命令。

## 非目标

- 不替代 IDE、AI Coding runtime、issue tracker 或 CI。
- 不要求所有成员使用同一种 Agent。
- 不把历史计划和过程报告作为当前实施入口。
- 不让 executor 自己批准最终 review。

## 项目事实层

目标项目的 `.governance/` 是运行时事实层。新会话或另一个 Agent 必须先读取：

- `.governance/AGENTS.md`
- `.governance/local/current-state.md`
- `.governance/agent-playbook.md`
- `.governance/changes/<change-id>/contract.yaml`
- `.governance/changes/<change-id>/bindings.yaml`

如果项目已经实施 open-cowork，Agent 应运行 `ocw activate` 读取项目级 activation 状态，不应重新从聊天历史推断。
