# 00. Overview

open-cowork 是一个 Agent-first collaboration governance protocol。它的作用对象是项目，而不是单个 Agent、单个会话或某个 IDE。

## 目标

- 让复杂任务从聊天意图进入项目级结构化事实。
- 让多个 Agent 能围绕同一个 active round 接续工作。
- 让 scope、owner、evidence、review、archive 和 continuity 可审计。
- 让人用自然语言发起和决策，而不是背 CLI 命令。
- 让已确认需求按完整范围推进；任何降级、拆分或延期都必须先获得人的明确批准并记录为事实。
- 让多个超级个体通过参与者登记、分派、阻塞、审查队列、摘要、carry-forward 和复盘资产形成可持续的团队操作循环。

## 非目标

- 不替代 IDE、AI Coding runtime、issue tracker 或 CI。
- 不要求所有成员使用同一种 Agent。
- 不把历史计划和过程报告作为当前实施入口。
- 不让 executor 自己批准最终 review。

## 完整实现原则

所有已确认的需求、round scope / `scope_in`、验收标准和任务完成定义，默认都要求完整实现。这是 open-cowork 的全流程治理原则，不是某个步骤的局部 gate。

Agent 不得未经人明确批准，把完整需求自行改写为最小实现、部分实现、延期实现或后续再补。若 Agent 发现范围过大、风险过高、依赖缺失或需要拆分，必须停在当前流程位置提出范围修订、拆分方案或阻断说明，并在项目事实中留下记录。只有在人明确批准后，才能调整范围、降级验收或把内容移入后续迭代。

未经批准的降级事实不能被 open-cowork 的任何流程环节消费：不能作为执行完成、evidence 成立、验证通过、review approve、closeout、archive、handoff 或 ledger 记录的依据。Reviewer 和后续接手 Agent 必须把未经批准的范围缩减、验收降级或任务遗漏视为阻塞问题，而不是可顺手补录的缺口。

## 执行前检查原则

已启用 open-cowork 的项目必须先治理、后执行。Agent / LLM 收到开发任务时，应先通过 activation / resume / preflight 确认当前 active round、scope、role bindings、external rules、execution gate 和 readiness。未通过 preflight 时，不得修改项目文件。

如果发现项目文件已经被修改但没有经过 open-cowork 流程，只能记录为 flow bypass recovery。Recovery 需要说明绕过原因、已修改文件、缺失的 scope / evidence / review / approval 和恢复动作；它不能伪装成正常执行证据，也不能替代完整实现原则。

## 项目事实层

目标项目的 `.governance/` 是运行时事实层。新会话或另一个 Agent 必须先读取：

- `.governance/AGENTS.md`
- `.governance/current-state.md`
- `.governance/agent-playbook.md`
- `.governance/state.yaml`

如果项目已经实施 open-cowork，Agent 应运行 `ocw activate` 读取项目级 activation 状态，不应重新从聊天历史推断。

## 团队操作循环原则

v0.3.9 起，`.governance/team/**` 是团队当前操作面的事实层。它记录可参与当前项目的本地个人域 Agent、远程团队成员 Agent、owner / executor / reviewer 分派、阻塞状态、审查队列、周期性意图、团队摘要、carry-forward 候选和复盘资产。

这些团队事实不能绕过 active round、scope、execution gate、evidence、verify、review、closeout 或 archive。它们的作用是让团队知道当前谁负责、谁被阻塞、谁需要审查、哪些事项需要下轮接续，而不是替代执行链路。
