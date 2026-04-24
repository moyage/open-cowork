# open-cowork Milestone 1 Change Package

## 1. 基本信息

- Change ID：`CHG-20260424-001`
- 标题：`Milestone 1 基线成立：复杂协作最小核心协议面落地`
- 所属版本策略：`1 个版本，2 个内部里程碑` 中的 `Milestone 1`
- 对应能力包：
  - `Package A` 全部
  - `Package B` 最小必要集
  - `Package C` 最小 continuity 能力
  - `Package E` 最小必要集
- 建议 policy level：`standard`
- 当前状态：`drafting`

## 2. 本 Change 的目的

本 Change 用于把 `open-cowork` 从“顶层定义已经澄清”推进到“新基线第一次真实成立”。

它不是一次大而全的升级，也不是把全部长期能力一次做完。
它只解决一个关键问题：

> 让 `open-cowork` 作为“面向多个超级个体协同的复杂协作底层框架与协议体系”，第一次具备真实可用的最小核心协议面。

## 3. 本 Change 必须回答的核心问题

1. 是否已经具备一条真实可走通的复杂协作闭环主链。
2. 是否已经有最小边界硬化，而不是只停留在口头约束。
3. 是否已经具备最小 continuity 能力，使任务在 session 中断后可恢复。
4. 是否已经同时具备最小人类状态面，使人和团队能看清当前阶段与下一步。

## 4. 范围定义

### 4.1 Scope In

本 Change 纳入以下范围：

1. 主链闭环最小成立
- `change create`
- `contract validate`
- `execute`
- `verify`
- `review`
- `archive`

2. 最小边界硬化
- Step 6 准入约束
- owner / reviewer / verifier separation
- 最小 write-boundary 保护
- 基本 state consistency

3. 最小 continuity 能力
- handoff / continuity packet
- 当前状态压缩输出
- 下一判断点与下一步输入

4. 最小人类状态面
- 默认 4 阶段视图
- `current_phase`
- `current_owner`
- `waiting_on`
- `next_decision`
- 项目中心状态摘要

5. 支撑这些能力的最小 CLI / 文件结构 / 状态输出

### 4.2 Scope Out

本 Change 明确不纳入以下范围：

1. 完整生态治理能力
2. 重型中心化产品壳或企业控制台
3. 多 adapter 生态与完整 marketplace
4. 完整 continuity primitives 全量能力
5. 深度 TUI / Dashboard 产品化
6. 主导型 cowork agent persona
7. 对所有历史规格文档的全面重写

## 5. 本 Change 的最小核心协议面

本 Change 完成后，至少必须成立以下最小核心协议面：

1. 结构化任务入口与 change package
2. execution contract 与角色绑定
3. `execute -> evidence -> verify -> review -> archive` 主链
4. 最小 continuity packet
5. 默认人类状态面

这 5 项是 `Milestone 1` 成立的判断基础。

## 6. 目标产物

本 Change 完成后，至少应产出以下结果：

1. 一条从 change 创建到 archive 的真实主链
2. 一组最小但真实可执行的 CLI 入口或等价调用链
3. 一份最小 continuity / handoff 输出
4. 一份默认人类状态快照输出
5. 一套可验证的状态与边界检查结果
6. 对应的测试与验证证据

## 7. 功能性要求

### R1. 主链闭环

系统必须支持从结构化 change 入口推进到 archive 收束，且中间经过可见的 contract、execute、verify、review 节点。

### R2. 主链不可绕过

在 `Milestone 1` 范围内，不允许通过跳过 verify / review / archive 来声称“已完成”。

### R3. 最小 continuity 输出

每次完成关键阶段后，必须能输出至少包含以下内容的 continuity packet：

- 当前阶段
- 当前 change
- 当前结论摘要
- 当前阻塞
- 下一判断点
- 下一步输入建议

### R4. 最小人类状态面

系统必须能输出一份默认给人阅读的状态摘要，而不是只输出底层 runtime artifacts。

### R5. 最小边界与角色秩序

执行者、验证者、审查者之间必须有最小角色隔离；写入边界与 Step 6 准入必须具备最小硬约束或最小稳定暴露。

## 8. 非功能性要求

### N1. 低侵入

不强迫个人域统一 Agent、模型、IDE、CLI 或本地工作流。

### N2. 中文默认文档

本 Change 相关的人类阅读文档默认使用中文。

### N3. 机器产物与人类产物分层

不得再把全部 runtime artifacts 直接当作人默认阅读入口。

### N4. 可恢复

在 session 压缩或会话切换后，必须能依靠 continuity 输出恢复推进，而不是依赖回放全部聊天历史。

## 9. 验收标准

### A1. 闭环成立

存在一条真实样例链路，能从 change 创建推进到 archive，并留下对应 evidence、verify、review、archive 产物。

### A2. 边界成立

至少能证明以下约束之一被真实执行，而不是只存在文档声明：

- Step 6 entry gate
- 角色分离检查
- 写入边界检查
- 状态一致性检查

### A3. continuity 成立

至少能产出一份足以支持下一会话继续推进的最小 continuity packet。

### A4. 人类状态面成立

至少能产出一份默认状态摘要，包含：

- 当前阶段
- 当前 owner
- waiting-on
- next decision
- 项目中心摘要

### A5. 文档与实现对齐

顶层文档、PRD、执行计划、change package 与实际实现行为之间不存在明显矛盾。

## 10. 风险与防漂移约束

### 风险 RSK1：主链做成占位串联而不是真实闭环

控制：
- 主链必须用真实输入输出与真实落盘产物验证。

### 风险 RSK2：只顾底层，不顾人类状态面

控制：
- 最小人类状态面纳入 `Milestone 1` 验收，而不是留到下一轮。

### 风险 RSK3：范围再次膨胀

控制：
- 严格按 `Milestone 1` 范围执行，不把 `Package D` 主体或完整 `Package C` 一次塞入。

### 风险 RSK4：文档和实现再次分叉

控制：
- 每一个新增命令、状态字段或产物结构，都必须能映射回执行计划中的“顶层判断 -> 第一轮交付物”。

## 11. 建议任务分组

### WG1. 主链工作组

负责：
- change create
- contract validate
- execute
- verify
- review
- archive

### WG2. 边界与状态工作组

负责：
- Step 6 entry
- 角色分离
- 最小 write-boundary
- state consistency

### WG3. continuity 与状态面工作组

负责：
- continuity packet
- 人类状态快照
- 4 阶段视图与项目中心摘要

## 12. 与后续里程碑的关系

本 Change 只让基线成立。

以下内容留给 `Milestone 2`：

- 更完整的 continuity primitives
- 更强的 adapter / protocol 层
- 更完整的 machine-readable timeline
- 更成熟的人类体验层
- 更深的工具接入与产品壳

## 13. 一句话结论

`CHG-20260424-001` 的目标，不是把 `open-cowork` 做大，而是让它第一次作为复杂协作底座真实成立。
