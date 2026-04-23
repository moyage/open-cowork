# open-cowork Milestone 2 需求收口与拆分

## 1. 文档目的

本文件用于在 `Milestone 1` 基线已经成立的前提下，对 `Milestone 2` 的需求范围进行一次正式收口。

它回答 4 个问题：

1. `Milestone 1` 到底已经完成到了哪里；
2. 哪些事项应正式进入 `Milestone 2`；
3. 哪些事项仍应继续延后，避免当前阶段失焦；
4. `Milestone 2` 应如何拆分，才能兼顾落地质量与后续持续迭代。

## 2. 当前基线判断

截至当前主线状态，`Milestone 1` 已经完成以下最小成立面：

1. 主链闭环成立  
   - `change create -> contract validate -> run -> verify -> review -> archive`
2. 主链不可绕过  
   - `review` 需要 `verify=pass`
   - `archive` 需要 `review=approve`
3. 最小边界硬化成立  
   - Step 6 entry gate
   - `executor / verifier / reviewer` 最小分离
   - 最小 write-boundary 产物路径校验
   - state consistency 基本检查
4. 最小 continuity 成立  
   - `continuity launch-input`
   - `continuity round-entry-summary`
   - 最小决策摘要字段
5. 最小人类状态面成立  
   - 4 阶段视图
   - `current_phase`
   - `current_owner`
   - `waiting_on`
   - `next_decision`
   - 项目中心摘要

因此，`Milestone 2` 不再需要重复解决“基线是否存在”这个问题，而应转向“如何把基线硬化成可持续扩展的协作框架”。

## 3. Milestone 2 的目标

`Milestone 2` 的目标不是继续堆功能，而是围绕以下 3 个方向做硬化与扩展：

1. 把当前的最小约束，推进为更稳定、更可信的约束；
2. 把当前的最小 continuity 与最小状态面，推进为可被外部系统消费的稳定协议输出；
3. 把单一最小 adapter MVP，推进为更明确的协议/适配层，而不把项目拉成重型平台。

一句话说：

> `Milestone 2` 解决的是“让第一版复杂协作底座从可用，走向稳定、可扩展、可接入”。

## 4. Milestone 2 Scope In

### M2-S1. 边界与状态进一步硬化

纳入：

1. 更强的 write-boundary 约束
   - 从“产物路径声明校验”推进到更强的实际写入约束
2. 状态迁移进一步收紧
   - 明确不可逆迁移与非法回退
   - 减少隐式状态修补
3. truth-source / artifact boundary 继续硬化
4. forbidden actions 规则继续具象化

### M2-S2. continuity primitives 完整化

纳入：

1. handoff package 正式结构
2. owner transfer continuity
3. increment package
4. standard state semantics
5. escalation / sync packet 的最小正式结构

### M2-S3. 协议与适配层主体

纳入：

1. tool-agnostic collaborator contract 细化
2. adapter contract 正式化
3. machine-readable runtime status 输出
4. timeline / progress API
5. 外部只读消费接口的最小稳定面

### M2-S4. 人类体验层深化

纳入：

1. 当前状态快照进一步丰富
2. `project delta / participants / human gate` 的默认可见性
3. operator-facing pack 进一步压缩和稳定
4. closeout / handoff 的人类默认阅读入口

## 5. Milestone 2 Scope Out

以下事项仍明确不纳入 `Milestone 2`：

1. 生态级治理与项目组合管理
2. 重型中心化平台或企业控制台
3. 深度 TUI / Dashboard 产品化
4. 多 adapter 生态全量扩张
5. Marketplace、账号体系、组织级工作台
6. 主导型 cowork agent persona
7. 把 `open-cowork` 拉成统一 AI Coding Runtime

## 6. 建议拆分方式

`Milestone 2` 不建议再按零散功能点推进，而建议拆成两个连续工作包。

### Workstream A：协议与约束硬化

目标：

- 先把当前最小基线做硬，避免后面建立在“可运行但不够稳”的基础上继续扩展。

建议纳入：

1. write-boundary 增强
2. 状态迁移不可逆约束
3. truth-source / artifact boundary 继续硬化
4. standard state semantics 初稿
5. handoff / increment / owner transfer 的最小正式结构

退出条件：

- 关键边界与关键迁移不再依赖“实现者自觉”维持。

### Workstream B：machine-readable 协议输出

目标：

- 把当前状态层和 continuity 层推进成稳定的、可被其他 agent / 工具 / 系统消费的协议输出。

建议纳入：

1. runtime status schema
2. timeline / progress API
3. participants / waiting-on / next-decision 的 machine-readable 输出
4. adapter contract 正式化
5. 外部只读消费接口最小集合

退出条件：

- 外部执行体或上层只读系统可以不解析人类阅读文档，直接消费结构化状态。

## 7. 优先级建议

### P0

1. 状态迁移不可逆约束
2. 更强的 write-boundary
3. handoff / owner transfer / increment package 的最小正式结构

### P1

1. runtime status schema
2. timeline / progress API
3. adapter contract 正式化
4. standard state semantics

### P2

1. 人类体验层深化项
2. 更完整的外部只读消费面
3. 更丰富的工具接入样例

## 8. 对后续迭代的直接约束

为了防止 `Milestone 2` 重新发散，后续实施必须遵守以下约束：

1. 先做 Workstream A，再做 Workstream B。
2. 不把产品壳、可视化壳层和平台化壳层提前混入当前轮。
3. 所有新增协议输出都必须有 schema、测试和迁移边界。
4. 所有新增人类状态输出都必须和 machine-readable 输出共享同一事实底座。
5. 不为了“看起来丰富”而提前扩张多 adapter 生态。

## 9. 建议作为下一轮启动输入的材料

下一轮正式启动前，建议把以下材料作为统一输入：

1. `docs/plans/01-execution-plan.md`
2. `docs/plans/04-milestone1-change-package.md`
3. 本文件 `docs/plans/06-milestone2-scope-and-splitting.md`
4. 当前主线测试通过结果
5. 当前 `Milestone 1` 已完成能力清单

## 10. 一句话结论

`Milestone 2` 的重点，不是“做更多东西”，而是把已经成立的复杂协作基线，推进成更稳定、更可信、可被外部消费和持续接入的协议层。
