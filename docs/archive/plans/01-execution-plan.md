# open-cowork 执行计划

## 1. 计划目标

把 `open-cowork` 从一套已经明确定位的公开基线，推进为一个能够被持续实践、持续复用、持续演进的复杂协作底层框架与协议体系。

## 2. 计划前提

后续迭代建立在以下前提之上：

1. `open-cowork` 的主身份是复杂协作底座，而不是某个单一范式标签。
2. 项目解决的是多个超级个体在复杂项目中的协同组织问题，而不是小范围的效率优化问题。
3. 个人域可以异构，但协作协议必须逐步统一。
4. 项目边界保持在项目级与任务级复杂协作，不扩张到生态级治理。
5. 后续所有实现都要同时兼顾机器可执行性和人类可理解性。

## 3. 执行原则

1. 先解决真实复杂协作问题，再讨论标签与包装。
2. 先统一协议与协作结构，再讨论工具或平台统一。
3. 先让闭环成立，再让边界变硬，再让连续性和人类体验跟上。
4. 不把项目拉向生态级治理。
5. 不让个人高手技巧继续成为唯一推进方式。
6. 文档定义、实现行为与产物结构必须持续对齐。

## 4. 能力包路线图

这里的 `Package A-E` 是能力包，不是发版包。

它们用于拆解问题空间、组织能力结构与约束讨论范围，但不应被机械理解为“一包一个版本”或“必须按包编号逐个发版”。

### Package A：复杂协作闭环主链

目标：

- 完成任务入口到归档接续的主链；
- 让复杂任务不再停留在“流程看起来存在”，而是真能稳定推进。

包含：

- 结构化入口与 change create
- contract validate
- execute
- verify
- review
- archive

退出条件：

- 一条完整主链可以产生真实的复杂协作闭环结果，而不是停留在 placeholder 提示或手工补洞状态。

### Package B：边界与状态硬化

目标：

- 让协作结构更像工程系统，而不是更长的对话。

包含：

- step-entry enforcement
- owner / reviewer / verifier 边界硬化
- 真实 write-boundary protection
- state transition consistency
- truth-source / artifact boundary
- forbidden actions 强化

退出条件：

- 关键治理违规不再只能事后解释，而能被稳定阻断或稳定暴露。

### Package C：连续性与协作原语

目标：

- 让复杂项目在 handoff、owner transfer、session 中断之后仍可接续。

包含：

- handoff package
- owner transfer continuity
- increment package
- standard state semantics
- startup packet
- escalation / sync packet

退出条件：

- 一个 change、一个任务或一个项目，可以在不回放原始聊天历史的情况下完成恢复与接力。

### Package D：协议与适配层

目标：

- 让 `open-cowork` 能作为协作协议层接入不同 Agent、不同 AI Coding 工具和不同执行体。

包含：

- tool-agnostic collaborator contract
- adapter contract
- machine-readable runtime status
- 只读消费接口
- 对外状态快照与 timeline 输出

退出条件：

- 不同个人域和不同工具栈可以在不被强制统一的前提下，围绕稳定协议接入同一复杂协作结构。

### Package E：人类协作体验层

目标：

- 把机器友好的底层结构翻译成人和团队也能理解、也愿意采用的默认体验。

包含：

- 默认 4 阶段视图与 9 步展开视图
- owner / participants / human gate 可见
- waiting-on / next decision / project delta 状态字段
- operator-facing reading pack
- 项目中心而非流程中心的默认汇报

退出条件：

- 人可在不通读全部 runtime artifacts 的前提下理解当前阶段、目标、阻塞与下一步；
- 团队可以用默认阅读包完成交接、审阅和阶段判断；
- 不再出现强烈的“盲盒式推进”体验。

## 5. 推荐发版策略：1 个版本，2 个内部里程碑

推荐采用：

- 对外 1 个版本
- 对内 2 个内部里程碑

不推荐把 `Package A-E` 机械拆成 5 个独立版本，因为这会显著增加主线漂移、阶段失焦和文档/实现反复分叉的风险。

### Milestone 1：基线成立

目标：

- 让 `open-cowork` 的新定位第一次以真实能力成立，而不是停留在定义层。

范围：

- `Package A` 全部
- `Package B` 最小必要集
- `Package E` 最小必要集
- `Package C` 的最小 continuity 能力

Milestone 1 至少应做到：

1. 主链闭环成立：`change -> contract -> execute -> verify -> review -> archive`
2. 关键边界开始具备真实阻断或真实暴露能力
3. 默认人类状态面成立：4 阶段视图、owner、waiting-on、next decision
4. 至少具备最小 handoff / continuity packet

### Milestone 2：硬化与扩展

目标：

- 在基线成立之后，把它补成更稳定、更可恢复、更可接不同工具与不同 Agent 的协作框架。

范围：

- `Package B` 剩余项
- `Package C` 完整原语
- `Package D` 主体
- `Package E` 深化项

Milestone 2 重点补齐：

1. 关键边界与状态进一步硬化
2. continuity primitives 完整化
3. 协议与适配层稳定化
4. 机器可读输出与人类体验层继续增强

## 6. 顶层判断到第一轮交付物的映射

| 顶层判断 | 第一轮必须落下的交付物 |
|---|---|
| `open-cowork` 是复杂协作底层框架，而不是概念集合 | 主链闭环命令与产物结构成立 |
| 个人域可以异构，但协作协议必须统一 | change package、contract、review/archive 结构固定化 |
| 多个超级个体协同需要边界与角色秩序 | owner / reviewer / verifier separation 与最小 write boundary |
| 复杂协作必须可接续，而不是靠回放聊天 | 最小 continuity packet 与 handoff 入口 |
| 默认体验必须对人清楚，而不是只对 Agent 清楚 | 4 阶段视图、current phase、owner、waiting-on、next decision |

## 7. 当前阶段重点

当前最重要的，不是马上拉长路线图，而是围绕以下三件事准备下一轮启动：

1. 保证顶层文档、产品定义与执行计划已经统一口径。
2. 锁定第一轮实施按 `Milestone 1` 收敛范围，而不是把 `Package A-E` 拆成多个版本。
3. 为后续 change package、设计包和任务拆解提供稳定输入。

## 8. 文档与产物要求

后续执行中的文档与产物需要遵守以下要求：

1. 机器产物和人类阅读产物分层组织。
2. 每轮默认阅读包保持压缩，不把十几个 runtime artifacts 全部直接推给人。
3. 每个阶段都要明确 owner、参与者、当前判断点和下一步。
4. 所有新文档默认使用中文，并保持与顶层定义一致。

## 9. 不在本计划中处理的事项

以下事项不在当前 `open-cowork` 执行计划中处理：

- 生态级治理、项目组合管理与跨项目裁决
- 重型中心化平台或企业级控制台建设
- 强绑定某一种 Agent、某一种 IDE 或某一种执行底座
- 为了展示而优先做大而全的壳层产品
